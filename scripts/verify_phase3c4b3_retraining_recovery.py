"""PostgreSQL recovery proof for explicit leased retraining execution."""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_execution import RETRAINING_MAX_ATTEMPTS, RETRAINING_TASK_ID, RetrainingExecutionService, RetrainingTrainingWorker
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.application.xgboost_challenger_training import XGBoostChallengerTrainingService
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore, RuntimeStoreLeaseError
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.services.model_artifact_storage import LocalModelArtifactStorage
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape


def _eligibility(fixture):
    session = SessionLocal()
    try:
        return next(row for row in RetrainingEligibilityService(session).evaluate(
            fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"],
        ) if row.material_code == fixture["material_code"])
    finally:
        session.close()


def _job(fixture):
    accepted = RetrainingJobService().accept_candidate(RetrainingJobRequest(
        fixture["company_id"], fixture["material_code"], fixture["demand_type"], fixture["start_period"], fixture["end_period"], "2026-W24", _eligibility(fixture),
    ))
    assert accepted.status == "CREATED"
    return accepted.job_id


def _start(fixture, job_id):
    result = RetrainingExecutionService().start(fixture["company_id"], job_id)
    assert result.status == "STARTED"
    return result


def _expire(fixture, job_id):
    session = SessionLocal()
    try:
        job = session.query(RetrainingJob).filter_by(id=job_id, company_id=fixture["company_id"]).one()
        task = session.query(RuntimeTask).filter_by(execution_id=job.runtime_execution_id, task_id=RETRAINING_TASK_ID).one()
        task.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()
    finally:
        session.close()


def _manual_claim(fixture, job_id, worker_id, heartbeat=False):
    session = SessionLocal()
    try:
        job = session.query(RetrainingJob).filter_by(id=job_id, company_id=fixture["company_id"]).one()
        store = RuntimeStore(session)
        execution = store.get_execution(job.runtime_execution_id, fixture["company_id"])
        if execution.state == "queued":
            execution = store.transition_execution(execution.execution_id, fixture["company_id"], "queued", "running", execution.row_version, current_stage="retraining")
        task = next(row for row in store.get_tasks(execution.execution_id, fixture["company_id"]) if row.task_id == RETRAINING_TASK_ID)
        claimed, attempt = store.claim_task(execution.execution_id, task.task_id, fixture["company_id"], worker_id, 30, task.row_version)
        if heartbeat:
            store.heartbeat_task(execution.execution_id, task.task_id, fixture["company_id"], claimed.lease_token, 30)
        job.state = "running"
        session.commit()
        return job.runtime_execution_id, task.task_id, claimed.lease_token, attempt.attempt_number
    finally:
        session.close()


class _BeforeArtifactFailure:
    def __init__(self, session):
        self.session = session
    def persist(self, request, result):
        raise RuntimeError("PROBE_PRE_ARTIFACT_FAILURE")


class _RetryableTrainingFailure:
    def __init__(self, session):
        self.session = session
    def train(self, request):
        raise RuntimeError("PROBE_RETRYABLE_TRAINING_FAILURE")


class _TerminalTrainingFailure:
    def __init__(self, session):
        self.session = session
    def train(self, request):
        raise ValueError("PROBE_INVALID_PERSISTED_EVIDENCE")


def _crash_after_artifact(job, artifact):
    raise SystemExit("PROBE_CRASH_AFTER_ARTIFACT_MARKER")


def _cleanup(root):
    session = SessionLocal()
    try:
        artifacts = session.query(ModelArtifact).filter_by(company_id=root["company_id"]).all()
        session.query(RetrainingJob).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        for artifact in artifacts:
            LocalModelArtifactStorage().delete_for_controlled_cleanup(artifact.artifact_storage_reference)
        session.query(ModelArtifact).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=root["company_id"], analysis_type="retraining")]
        if execution_ids:
            task_ids = [row[0] for row in session.query(RuntimeTask.id).filter(RuntimeTask.execution_id.in_(execution_ids))]
            if task_ids:
                session.query(RuntimeResultReference).filter(RuntimeResultReference.runtime_task_id.in_(task_ids)).delete(synchronize_session=False)
                session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.runtime_task_id.in_(task_ids)).delete(synchronize_session=False)
            session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(execution_ids)).delete(synchronize_session=False)
            session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).delete(synchronize_session=False)
            session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        session.commit()
        cleanup_fixture(session, type("FixtureIds", (), root)())
    finally:
        session.close()


async def main():
    roots = []
    original_fit = xgboost.XGBRegressor.fit
    fits = {"count": 0}
    def counted_fit(*args, **kwargs):
        fits["count"] += 1
        return original_fit(*args, **kwargs)
    xgboost.XGBRegressor.fit = counted_fit
    try:
        control = await create_tier_shape("tier3", 8, "CONTROL", "sales")
        roots.append(control)
        context = {key: control[key] for key in ("company_id", "user_id", "dataset_id")}
        race = await create_tier_shape("tier3", 8, "RACE", "sales", context=context)
        pre_artifact = await create_tier_shape("tier3", 8, "PRE", "sales", context=context)
        post_artifact = await create_tier_shape("tier3", 8, "POST", "sales", context=context)
        lease = await create_tier_shape("tier3", 8, "LEASE", "sales", context=context)
        heartbeat = await create_tier_shape("tier3", 8, "HEART", "sales", context=context)
        retry = await create_tier_shape("tier3", 8, "RETRY", "sales", context=context)
        exhausted = await create_tier_shape("tier3", 8, "EXHAUST", "sales", context=context)
        terminal = await create_tier_shape("tier3", 8, "TERMINAL", "sales", context=context)

        # A: normal control.
        control_job = _job(control); _start(control, control_job)
        control_result = RetrainingTrainingWorker(worker_id="control").run(control["company_id"], control_job)
        assert control_result.status == "TRAINED"

        # B/D: true ModelArtifact unique-fingerprint race returns one durable artifact.
        race_job = _job(race)
        session = SessionLocal()
        try:
            job = session.query(RetrainingJob).filter_by(id=race_job, company_id=race["company_id"]).one()
            request = RetrainingTrainingWorker._request(job)
            trained = XGBoostChallengerTrainingService(session).train(request)
            assert trained.status == "TRAINED"
        finally:
            session.close()
        def persist_once(_):
            candidate_session = SessionLocal()
            try:
                persisted = XGBoostChallengerArtifactService(candidate_session).persist(request, trained)
                artifact_id, created = persisted.artifact.id, persisted.created
                candidate_session.commit()
                return artifact_id, created
            finally:
                candidate_session.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            persisted = list(pool.map(persist_once, range(2)))
        assert len({row[0] for row in persisted}) == 1
        assert sorted(row[1] for row in persisted) == [False, True]

        # C: success before artifact persistence fails; a fresh retry fits and completes.
        pre_job = _job(pre_artifact); _start(pre_artifact, pre_job)
        pre_first = RetrainingTrainingWorker(worker_id="pre-failure", artifact_service_factory=_BeforeArtifactFailure).run(pre_artifact["company_id"], pre_job)
        assert pre_first.status == "RETRY_SCHEDULED"
        session = SessionLocal()
        try:
            assert session.query(RetrainingJob).filter_by(id=pre_job).one().model_artifact_id is None
        finally:
            session.close()
        pre_second = RetrainingTrainingWorker(worker_id="pre-retry").run(pre_artifact["company_id"], pre_job)
        assert pre_second.status == "TRAINED"

        # D/N: durable artifact marker survives a process crash and is reused without a second fit.
        post_job = _job(post_artifact); _start(post_artifact, post_job)
        before_post_fit = fits["count"]
        try:
            RetrainingTrainingWorker(worker_id="post-crash", post_artifact_persisted_hook=_crash_after_artifact).run(post_artifact["company_id"], post_job)
            raise AssertionError("post-artifact crash hook did not stop worker")
        except SystemExit:
            pass
        session = SessionLocal()
        try:
            marked = session.query(RetrainingJob).filter_by(id=post_job, company_id=post_artifact["company_id"]).one()
            assert marked.state == "running" and marked.model_artifact_id is not None
            artifact_id = marked.model_artifact_id
        finally:
            session.close()
        _expire(post_artifact, post_job)
        recovered = RetrainingTrainingWorker(worker_id="post-recovery").run(post_artifact["company_id"], post_job)
        assert recovered.status == "TRAINED" and recovered.artifact_id == artifact_id and fits["count"] == before_post_fit + 1

        # E/F: expired lease is reclaimed; the stale worker's old token cannot complete.
        lease_job = _job(lease); _start(lease, lease_job)
        lease_execution_id, lease_task_id, stale_token, _ = _manual_claim(lease, lease_job, "stale-worker")
        _expire(lease, lease_job)
        lease_result = RetrainingTrainingWorker(worker_id="reclaimer").run(lease["company_id"], lease_job)
        assert lease_result.status == "TRAINED" and lease_result.attempt_number == 2
        session = SessionLocal()
        try:
            try:
                RuntimeStore(session).complete_task_attempt(lease_execution_id, lease_task_id, lease["company_id"], stale_token, "retraining", {"late": True})
                raise AssertionError("stale worker completed")
            except RuntimeStoreLeaseError:
                session.rollback()
        finally:
            session.close()

        # G: an active heartbeat retains the lease; another worker sees no work.
        heartbeat_job = _job(heartbeat); _start(heartbeat, heartbeat_job)
        _manual_claim(heartbeat, heartbeat_job, "healthy-worker", heartbeat=True)
        before_heartbeat_fit = fits["count"]
        assert RetrainingTrainingWorker(worker_id="contender").run(heartbeat["company_id"], heartbeat_job).status == "NO_WORK"
        assert fits["count"] == before_heartbeat_fit
        _expire(heartbeat, heartbeat_job)
        assert RetrainingTrainingWorker(worker_id="heartbeat-recovery").run(heartbeat["company_id"], heartbeat_job).status == "TRAINED"

        # H: a retryable worker failure followed by a fresh normal worker succeeds.
        retry_job = _job(retry); _start(retry, retry_job)
        retry_first = RetrainingTrainingWorker(worker_id="retry-fail", training_service_factory=_RetryableTrainingFailure).run(retry["company_id"], retry_job)
        retry_second = RetrainingTrainingWorker(worker_id="retry-success").run(retry["company_id"], retry_job)
        assert (retry_first.status, retry_second.status) == ("RETRY_SCHEDULED", "TRAINED")

        # I/L: exhausted transient failure and deterministic terminal failure have no re-entry work.
        exhausted_job = _job(exhausted); _start(exhausted, exhausted_job)
        bad_worker = RetrainingTrainingWorker(worker_id="exhaust", training_service_factory=_RetryableTrainingFailure)
        assert [bad_worker.run(exhausted["company_id"], exhausted_job).status for _ in range(RETRAINING_MAX_ATTEMPTS)] == ["RETRY_SCHEDULED", "FAILED"]
        terminal_job = _job(terminal); _start(terminal, terminal_job)
        terminal_result = RetrainingTrainingWorker(worker_id="terminal", training_service_factory=_TerminalTrainingFailure).run(terminal["company_id"], terminal_job)
        assert terminal_result.status == "FAILED"
        assert RetrainingExecutionService().start(exhausted["company_id"], exhausted_job).status == "ALREADY_COMPLETED"
        assert RetrainingTrainingWorker(worker_id="failed-reentry").run(exhausted["company_id"], exhausted_job).status == "ALREADY_COMPLETED"

        session = SessionLocal()
        try:
            jobs = session.query(RetrainingJob).filter_by(company_id=control["company_id"]).all()
            for job in jobs:
                execution = session.query(RuntimeExecution).filter_by(execution_id=job.runtime_execution_id, company_id=job.company_id).one_or_none()
                if execution is None:
                    assert job.state == "pending" and job.runtime_execution_id is None
                    continue
                tasks = session.query(RuntimeTask).filter_by(execution_id=job.runtime_execution_id, company_id=job.company_id).all()
                active_attempts = session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id == job.runtime_execution_id, RuntimeTaskAttempt.state == "running").count()
                assert not (job.state == "trained" and job.model_artifact_id is None)
                assert not (job.state == "trained" and execution.state != "completed")
                assert not (execution.state == "completed" and job.state not in ("trained", "not_trainable"))
                assert not (job.state == "failed" and any(task.state == "running" for task in tasks))
                assert active_attempts == 0
            assert session.query(ModelArtifact).filter_by(company_id=control["company_id"], material_code="RACE").count() == 1
            assert session.query(ChampionChallengerDecision).filter_by(company_id=control["company_id"]).count() == 0
            assert session.query(ChampionRegistryEntry).filter_by(company_id=control["company_id"]).count() == 0
            assert session.query(ChampionRegistryCurrent).filter_by(company_id=control["company_id"]).count() == 0
            assert session.query(ChampionRegistryTransition).filter_by(company_id=control["company_id"]).count() == 0
            assert session.query(CompanyLearningMemory).filter_by(company_id=control["company_id"]).count() == 0
            assert session.query(UserLearningData).filter_by(company_id=control["company_id"]).count() == 0
        finally:
            session.close()
        print("PHASE3C4B3 PASS", {
            "fit_calls": fits["count"], "artifact_race": [row[1] for row in persisted],
            "post_artifact_reused": str(artifact_id), "lease_reclaim_attempt": lease_result.attempt_number,
            "heartbeat": "NO_WORK", "retry": [retry_first.status, retry_second.status],
            "exhausted": "FAILED", "terminal": terminal_result.failure_code,
        })
    finally:
        xgboost.XGBRegressor.fit = original_fit
        company_ids = {root["company_id"] for root in roots}
        for root in roots:
            _cleanup(root)
        session = SessionLocal()
        try:
            assert session.query(Company).filter(Company.id.in_(company_ids)).count() == 0, "synthetic company residue remains"
        finally:
            session.close()


if __name__ == "__main__":
    asyncio.run(main())
