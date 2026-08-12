"""PostgreSQL proof for explicit leased Tier-3 RetrainingJob execution."""

import asyncio
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_execution import RETRAINING_CAPABILITY, RETRAINING_MAX_ATTEMPTS, RETRAINING_TASK_ID, RetrainingExecutionService, RetrainingTrainingWorker
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.services.model_artifact_storage import LocalModelArtifactStorage
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape


def _eligibility(fixture):
    session = SessionLocal()
    try:
        rows = RetrainingEligibilityService(session).evaluate(
            fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"],
        )
        return next(row for row in rows if row.material_code == fixture["material_code"])
    finally:
        session.close()


def _job_request(fixture, evidence, cutoff="2026-W24"):
    return RetrainingJobRequest(
        fixture["company_id"], fixture["material_code"], fixture["demand_type"], fixture["start_period"], fixture["end_period"], cutoff, evidence,
    )


def _counts(company_id):
    session = SessionLocal()
    try:
        return {
            "actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
            "revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
            "vintages": session.query(ForecastVintage).filter_by(company_id=company_id).count(),
            "evaluations": session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
            "runtime_executions": session.query(RuntimeExecution).filter_by(company_id=company_id).count(),
            "runtime_tasks": session.query(RuntimeTask).filter_by(company_id=company_id).count(),
            "runtime_attempts": session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
            "runtime_results": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
            "artifacts": session.query(ModelArtifact).filter_by(company_id=company_id).count(),
            "decisions": session.query(ChampionChallengerDecision).filter_by(company_id=company_id).count(),
            "registry_entries": session.query(ChampionRegistryEntry).filter_by(company_id=company_id).count(),
            "registry_current": session.query(ChampionRegistryCurrent).filter_by(company_id=company_id).count(),
            "registry_transitions": session.query(ChampionRegistryTransition).filter_by(company_id=company_id).count(),
            "company_learning": session.query(CompanyLearningMemory).filter_by(company_id=company_id).count(),
            "user_learning": session.query(UserLearningData).filter_by(company_id=company_id).count(),
        }
    finally:
        session.close()


class _RaisingTrainingService:
    def __init__(self, session):
        self.session = session

    def train(self, request):
        raise RuntimeError("PROBE_RETRYABLE_TRAINING_FAILURE")


def _cleanup(root):
    session = SessionLocal()
    try:
        artifacts = session.query(ModelArtifact).filter_by(company_id=root["company_id"]).all()
        for artifact in artifacts:
            LocalModelArtifactStorage().delete_for_controlled_cleanup(artifact.artifact_storage_reference)
        session.query(RetrainingJob).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        session.query(ModelArtifact).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=root["company_id"], analysis_type="retraining")]
        # The canonical fixture cleanup owns source Forecast evidence; clear B2 task dependencies only.
        task_ids = [row[0] for row in session.query(RuntimeTask.id).filter(RuntimeTask.company_id == root["company_id"], RuntimeTask.execution_id.in_(execution_ids))]
        if task_ids:
            session.query(RuntimeResultReference).filter(RuntimeResultReference.runtime_task_id.in_(task_ids)).delete(synchronize_session=False)
            session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.runtime_task_id.in_(task_ids)).delete(synchronize_session=False)
        if execution_ids:
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
    fit_calls = {"count": 0}
    def counted_fit(*args, **kwargs):
        fit_calls["count"] += 1
        time.sleep(0.75)
        return original_fit(*args, **kwargs)
    xgboost.XGBRegressor.fit = counted_fit
    try:
        success = await create_tier_shape("tier3", 8, "SUCCESS", "sales")
        roots.append(success)
        context = {key: success[key] for key in ("company_id", "user_id", "dataset_id")}
        not_trainable = await create_tier_shape("tier3", 8, "SHORT", "sales", context=context)
        failing = await create_tier_shape("tier3", 8, "FAIL", "sales", context=context)
        other_company = await create_tier_shape("tier3", 8, "OTHER", "sales")
        roots.append(other_company)

        jobs = RetrainingJobService()
        success_job = jobs.accept_candidate(_job_request(success, _eligibility(success)))
        not_trainable_job = jobs.accept_candidate(_job_request(not_trainable, _eligibility(not_trainable), "2026-W12"))
        failing_job = jobs.accept_candidate(_job_request(failing, _eligibility(failing)))
        other_job = jobs.accept_candidate(_job_request(other_company, _eligibility(other_company)))
        assert all(row.status == "CREATED" for row in (success_job, not_trainable_job, failing_job, other_job))

        # A/D: independent callers race to explicitly start the same pending job.
        barrier = threading.Barrier(2)
        def starter():
            barrier.wait()
            return RetrainingExecutionService().start(success["company_id"], success_job.job_id)
        with ThreadPoolExecutor(max_workers=2) as pool:
            starts = list(pool.map(lambda _: starter(), range(2)))
        assert sorted(row.status for row in starts) == ["ALREADY_STARTED", "STARTED"]
        started = next(row for row in starts if row.status == "STARTED")
        session = SessionLocal()
        try:
            runtime = session.query(RuntimeExecution).filter_by(execution_id=started.runtime_execution_id, company_id=success["company_id"]).one()
            tasks = session.query(RuntimeTask).filter_by(execution_id=runtime.execution_id, company_id=success["company_id"]).all()
            assert runtime.analysis_type == "retraining" and len(tasks) == 1
            assert tasks[0].task_id == RETRAINING_TASK_ID and tasks[0].capability == RETRAINING_CAPABILITY and tasks[0].max_attempts == RETRAINING_MAX_ATTEMPTS
            assert tasks[0].metrics["retraining_job_id"] == str(success_job.job_id)
            assert RetrainingExecutionService().start(other_company["company_id"], success_job.job_id).status == "NOT_EXECUTABLE"
        finally:
            session.close()

        # E/F/G/H/M: fresh workers race the same lease; only its owner fits and persists an artifact.
        worker_barrier = threading.Barrier(2)
        def worker(name):
            worker_barrier.wait()
            return RetrainingTrainingWorker(worker_id=name).run(success["company_id"], success_job.job_id)
        with ThreadPoolExecutor(max_workers=2) as pool:
            worker_results = list(pool.map(worker, ("worker-a", "worker-b")))
        trained = next(row for row in worker_results if row.status == "TRAINED")
        other_worker = next(row for row in worker_results if row is not trained)
        assert other_worker.status in ("NO_WORK", "ALREADY_COMPLETED") and fit_calls["count"] == 1
        session = SessionLocal()
        try:
            job = session.query(RetrainingJob).filter_by(id=success_job.job_id, company_id=success["company_id"]).one()
            artifact = session.query(ModelArtifact).filter_by(id=job.model_artifact_id, company_id=success["company_id"]).one()
            execution = session.query(RuntimeExecution).filter_by(execution_id=job.runtime_execution_id, company_id=success["company_id"]).one()
            task = session.query(RuntimeTask).filter_by(execution_id=execution.execution_id, task_id=RETRAINING_TASK_ID).one()
            attempt = session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task.id, attempt_number=1).one()
            assert job.state == "trained" and execution.state == "completed" and task.state == "completed" and attempt.duration_ms is not None
            assert artifact.eligibility_evidence["retraining_job_id"] == str(job.id) and artifact.artifact_checksum
            assert session.query(ChampionChallengerDecision).filter_by(company_id=success["company_id"]).count() == 0
            assert session.query(ChampionRegistryEntry).filter_by(company_id=success["company_id"]).count() == 0
        finally:
            session.close()
        assert RetrainingExecutionService().start(success["company_id"], success_job.job_id).status == "ALREADY_COMPLETED"
        assert RetrainingTrainingWorker(worker_id="reentry").run(success["company_id"], success_job.job_id).status == "ALREADY_COMPLETED"
        assert fit_calls["count"] == 1

        # I: Tier 3 job with a cutoff-safe but too-small history is terminal, not an infrastructure failure.
        start_short = RetrainingExecutionService().start(not_trainable["company_id"], not_trainable_job.job_id)
        short_result = RetrainingTrainingWorker(worker_id="short-worker").run(not_trainable["company_id"], not_trainable_job.job_id)
        assert start_short.status == "STARTED" and short_result.status == "NOT_TRAINABLE" and fit_calls["count"] == 1

        # J: retryable failure consumes a bounded two-attempt policy before a terminal job failure.
        assert RetrainingExecutionService().start(failing["company_id"], failing_job.job_id).status == "STARTED"
        bad_worker = RetrainingTrainingWorker(worker_id="failing-worker", training_service_factory=_RaisingTrainingService)
        first_failure = bad_worker.run(failing["company_id"], failing_job.job_id)
        second_failure = bad_worker.run(failing["company_id"], failing_job.job_id)
        assert (first_failure.status, second_failure.status) == ("RETRY_SCHEDULED", "FAILED")
        session = SessionLocal()
        try:
            failed_job = session.query(RetrainingJob).filter_by(id=failing_job.job_id, company_id=failing["company_id"]).one()
            failed_execution = session.query(RuntimeExecution).filter_by(execution_id=failed_job.runtime_execution_id, company_id=failing["company_id"]).one()
            failed_task = session.query(RuntimeTask).filter_by(execution_id=failed_execution.execution_id, task_id=RETRAINING_TASK_ID).one()
            assert (failed_job.state, failed_execution.state, failed_task.state, failed_task.current_attempt, failed_task.max_attempts) == ("failed", "failed", "failed", 2, RETRAINING_MAX_ATTEMPTS)
        finally:
            session.close()

        counts = _counts(success["company_id"])
        assert counts["actuals"] == 96 and counts["vintages"] == 3 and counts["evaluations"] == 1
        assert counts["decisions"] == counts["registry_entries"] == counts["registry_current"] == counts["registry_transitions"] == counts["company_learning"] == counts["user_learning"] == 0
        print("PHASE3C4B2 PASS", {
            "start": sorted(row.status for row in starts), "worker_claim": sorted(row.status for row in worker_results),
            "fit_calls": fit_calls["count"], "artifact_id": str(trained.artifact_id), "not_trainable": short_result.failure_code,
            "retry": [first_failure.status, second_failure.status], "max_attempts": RETRAINING_MAX_ATTEMPTS,
            "runtime_observability": {"attempt": trained.attempt_number, "task_id": str(trained.task_id)},
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
