"""Final PostgreSQL closeout for durable selective-retraining orchestration."""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.forecast_evaluation_service import ForecastEvaluationService
from app.application.retraining_execution import RetrainingTrainingWorker
from app.application.retraining_scheduler import RetrainingScannerSchedulerService
from app.application.retraining_scanner import RetrainingScannerService
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.retraining_resource_lease import RetrainingResourceLease
from app.models.retraining_scheduler_tick import RetrainingSchedulerTick
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.services.model_artifact_storage import LocalModelArtifactStorage
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape


class _FailingScanner:
    def __init__(self, *args, **kwargs): pass
    def scan_and_activate(self, *args, **kwargs): raise RuntimeError("PROBE_TICK_LEVEL_FAILURE")


class _RetryableTrainingFailure:
    def __init__(self, session): self.session = session
    def train(self, request): raise RuntimeError("PROBE_TRAINING_FAILURE")


def _correct(fixture, quantity, approve):
    service = ActualWeeklyLedgerService()
    proposed = service.ingest_dataset_actuals(fixture["company_id"], fixture["user_id"], fixture["dataset_id"], [{
        "material_code": fixture["material_code"], "period": fixture["end_period"], "quantity": quantity,
        "product_level": fixture["product_level"], "product_group": "G", "product_class": "C",
    }], fixture["demand_type"])
    decision = service.approve_revision if approve else service.reject_revision
    decision(fixture["company_id"], proposed["revision_ids"][0], fixture["user_id"])
    session = SessionLocal()
    try:
        ForecastEvaluationService(session).evaluate(fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"])
        session.commit()
    finally: session.close()


def _cleanup(root):
    session = SessionLocal()
    try:
        cid = root["company_id"]
        artifacts = session.query(ModelArtifact).filter_by(company_id=cid).all()
        execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=cid, analysis_type="retraining")]
        session.query(RetrainingSchedulerTick).filter_by(company_id=cid).delete(synchronize_session=False)
        session.query(RetrainingResourceLease).filter_by(company_id=cid).delete(synchronize_session=False)
        session.query(RetrainingJob).filter_by(company_id=cid).delete(synchronize_session=False)
        for artifact in artifacts:
            LocalModelArtifactStorage().delete_for_controlled_cleanup(artifact.artifact_storage_reference)
        session.query(ModelArtifact).filter_by(company_id=cid).delete(synchronize_session=False)
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
    finally: session.close()


def _tick(service, fixture, at, **kwargs):
    return service.run_tick(fixture["company_id"], fixture["start_period"], fixture["end_period"], scheduled_for=at,
                            cadence_seconds=60, **kwargs)


async def main():
    roots = []
    original_fit = xgboost.XGBRegressor.fit
    fits = {"count": 0}
    xgboost.XGBRegressor.fit = lambda *a, **kw: (fits.__setitem__("count", fits["count"] + 1), original_fit(*a, **kw))[1]
    try:
        # B/C: durable tick -> B5B start -> B2/B3 worker -> immutable artifact.
        root = await create_tier_shape("tier3", 8, "E2E", "sales"); roots.append(root)
        at = datetime(2026, 8, 12, 12, 0, 7, tzinfo=timezone.utc)
        scheduler = RetrainingScannerSchedulerService(cooldown_seconds=600, capacity=1)
        first = _tick(scheduler, root, at, owner_id="tick-a")
        assert first.status == "COMPLETED" and len(first.activation_report.activated) == 1
        scope = first.activation_report.activated[0]
        assert scope.admission_status == "STARTED"
        # Same delivery and two independent callers converge without duplicate work.
        assert _tick(RetrainingScannerSchedulerService(cooldown_seconds=600, capacity=1), root, at + timedelta(seconds=20), owner_id="dup").status == "ALREADY_COMPLETED"
        next_bucket = at + timedelta(minutes=1)
        def concurrent(owner):
            return _tick(RetrainingScannerSchedulerService(cooldown_seconds=600, capacity=1), root, next_bucket, owner_id=owner)
        with ThreadPoolExecutor(max_workers=2) as pool:
            concurrent_results = list(pool.map(concurrent, ("concurrent-a", "concurrent-b")))
        assert sum(row.status == "COMPLETED" for row in concurrent_results) == 1
        assert sum(row.status in ("ALREADY_RUNNING", "ALREADY_COMPLETED") for row in concurrent_results) == 1
        trained = RetrainingTrainingWorker(worker_id="e2e-worker", capacity=1).run(root["company_id"], scope.job_id)
        assert trained.status == "TRAINED" and fits["count"] == 1
        session = SessionLocal()
        try:
            job = session.query(RetrainingJob).filter_by(id=scope.job_id, company_id=root["company_id"]).one()
            assert job.state == "trained" and job.model_artifact_id == trained.artifact_id
            assert session.query(RuntimeExecution).filter_by(company_id=root["company_id"], analysis_type="retraining").count() == 1
            assert session.query(RuntimeTask).filter_by(execution_id=job.runtime_execution_id).count() == 1
            assert session.query(RetrainingResourceLease).filter_by(retraining_job_id=job.id, active=True).count() == 0
            first_ids = (job.id, job.candidate_fingerprint, job.runtime_execution_id, job.model_artifact_id)
        finally: session.close()

        # D: a later bucket with unchanged evidence is not a reason to retrain.
        same = _tick(RetrainingScannerSchedulerService(cooldown_seconds=600, capacity=1), root, at + timedelta(minutes=2), owner_id="same")
        assert same.status == "COMPLETED"
        session = SessionLocal()
        try:
            assert session.query(RetrainingJob).filter_by(company_id=root["company_id"]).count() == 1
            assert session.query(ModelArtifact).filter_by(company_id=root["company_id"]).count() == 1 and fits["count"] == 1
        finally: session.close()

        # E/F/G: accepted correction makes B1 evidence new; cooldown preserves
        # J2 without runtime/lease/model work. Rejected correction changes none.
        _correct(root, 220, approve=True)
        cooled_tick = _tick(RetrainingScannerSchedulerService(cooldown_seconds=600, capacity=1), root, at + timedelta(minutes=3), owner_id="corrected")
        cooled_scope = next(row for row in cooled_tick.activation_report.activated if row.material_code == "E2E")
        assert cooled_scope.admission_status == "COOLDOWN"
        session = SessionLocal()
        try:
            j2 = session.query(RetrainingJob).filter_by(id=cooled_scope.job_id, company_id=root["company_id"]).one()
            assert j2.id != first_ids[0] and j2.candidate_fingerprint != first_ids[1] and j2.runtime_execution_id is None
            assert session.query(RetrainingResourceLease).filter_by(retraining_job_id=j2.id).count() == 0
            j2_id, j2_fingerprint = j2.id, j2.candidate_fingerprint
        finally: session.close()
        _correct(root, 280, approve=False)
        rejected_tick = _tick(RetrainingScannerSchedulerService(cooldown_seconds=600, capacity=1), root, at + timedelta(minutes=4), owner_id="rejected")
        rejected_scope = next(row for row in rejected_tick.activation_report.activated if row.material_code == "E2E")
        assert rejected_scope.job_id == j2_id and rejected_scope.candidate_fingerprint == j2_fingerprint
        # Synthetic expiry alters only the policy clock anchor; the candidate ID
        # and correction-safe evidence remain the same, then existing B2 starts it.
        session = SessionLocal()
        try:
            session.query(RetrainingJob).filter_by(id=first_ids[0]).update({"completed_at": datetime.now(timezone.utc) - timedelta(seconds=601)})
            session.commit()
        finally: session.close()
        eligible_tick = _tick(RetrainingScannerSchedulerService(cooldown_seconds=600, capacity=1), root, at + timedelta(minutes=5), owner_id="expired")
        eligible_scope = next(row for row in eligible_tick.activation_report.activated if row.material_code == "E2E")
        assert eligible_scope.job_id == j2_id and eligible_scope.admission_status == "STARTED"
        assert RetrainingTrainingWorker(worker_id="second-worker", capacity=1).run(root["company_id"], j2_id).status == "TRAINED"
        assert fits["count"] == 2

        # H: existing B4 ordering/capacity retains a blocked candidate for later.
        priority = await create_tier_shape("tier3", 8, "LOW", "sales"); roots.append(priority)
        pctx = {key: priority[key] for key in ("company_id", "user_id", "dataset_id")}
        high = await create_tier_shape("tier3", 8, "HIGH", "sales", context=pctx)
        scanner = RetrainingScannerService(capacity=1)
        scanner.scan(priority["company_id"], priority["start_period"], priority["end_period"])
        session = SessionLocal()
        try:
            session.query(RetrainingJob).filter_by(company_id=priority["company_id"], material_code="LOW").update({"sample_count": 10})
            session.query(RetrainingJob).filter_by(company_id=priority["company_id"], material_code="HIGH").update({"sample_count": 30})
            session.commit()
        finally: session.close()
        cap_tick = _tick(RetrainingScannerSchedulerService(capacity=1), priority, at, owner_id="priority")
        outcomes = {row.material_code: row.admission_status for row in cap_tick.activation_report.activated}
        assert outcomes == {"HIGH": "STARTED", "LOW": "CAPACITY_BLOCKED"}
        session = SessionLocal()
        try:
            low = session.query(RetrainingJob).filter_by(company_id=priority["company_id"], material_code="LOW").one()
            assert low.runtime_execution_id is None
            session.query(RetrainingResourceLease).filter_by(company_id=priority["company_id"], active=True).update(
                {"active": False, "released_at": datetime.now(timezone.utc), "release_reason_code": "PROBE_CAPACITY_BOUNDARY"}, synchronize_session=False)
            session.commit()
        finally: session.close()

        # I/J: tick failure is distinct from a worker failure. A worker's two
        # retryable attempts terminalize only its job; its tick stays completed.
        failed_tick = _tick(RetrainingScannerSchedulerService(scanner_factory=_FailingScanner), priority, at + timedelta(minutes=10), owner_id="tick-fail")
        assert failed_tick.status == "FAILED"
        training = await create_tier_shape("tier3", 8, "TRAINFAIL", "sales"); roots.append(training)
        train_tick = _tick(RetrainingScannerSchedulerService(capacity=1), training, at, owner_id="train-fail")
        train_scope = train_tick.activation_report.activated[0]
        bad = RetrainingTrainingWorker(worker_id="bad", capacity=1, training_service_factory=_RetryableTrainingFailure)
        assert [bad.run(training["company_id"], train_scope.job_id).status for _ in range(2)] == ["RETRY_SCHEDULED", "FAILED"]
        session = SessionLocal()
        try:
            assert session.query(RetrainingSchedulerTick).filter_by(id=train_tick.tick_id).one().state == "completed"
            assert session.query(RetrainingJob).filter_by(id=train_scope.job_id).one().state == "failed"
        finally: session.close()

        # K/L/P/Q: persisted primitive-ID reconstruction, tenant separation,
        # correlation chain, and zero governance after scheduler-created artifacts.
        other = await create_tier_shape("tier3", 8, "OTHER", "sales"); roots.append(other)
        other_tick = _tick(RetrainingScannerSchedulerService(capacity=1), other, at, owner_id="other")
        assert other_tick.status == "COMPLETED" and other_tick.tick_id != first.tick_id
        session = SessionLocal()
        try:
            tick = session.query(RetrainingSchedulerTick).filter_by(id=first.tick_id, company_id=root["company_id"]).one()
            first_job = session.query(RetrainingJob).filter_by(id=first_ids[0], company_id=root["company_id"]).one()
            runtime = session.query(RuntimeExecution).filter_by(execution_id=first_ids[2], company_id=root["company_id"]).one()
            task = session.query(RuntimeTask).filter_by(execution_id=runtime.execution_id).one()
            artifact = session.query(ModelArtifact).filter_by(id=first_ids[3], company_id=root["company_id"]).one()
            assert tick.state == "completed" and tick.report_summary["activated"] == 1
            assert first_job.candidate_fingerprint == first_ids[1] and first_job.priority_policy_version
            assert runtime.metadata_["retraining_job_id"] == str(first_job.id) and task.task_id == "xgboost_challenger_train"
            assert artifact.artifact_checksum and artifact.artifact_fingerprint
            assert session.query(RetrainingSchedulerTick).filter_by(company_id=other["company_id"]).count() == 1
            assert session.query(ChampionChallengerDecision).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(ChampionRegistryEntry).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(ChampionRegistryCurrent).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(ChampionRegistryTransition).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(CompanyLearningMemory).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(UserLearningData).filter_by(company_id=root["company_id"]).count() == 0
        finally: session.close()
        print("PHASE3C4B5C2 PASS", {"fits": fits["count"], "tick": str(first.tick_id), "job": str(first_ids[0]),
              "artifact": str(first_ids[3]), "concurrent": [row.status for row in concurrent_results], "capacity": outcomes})
    finally:
        xgboost.XGBRegressor.fit = original_fit
        seen = set()
        for root in roots:
            if root["company_id"] not in seen:
                seen.add(root["company_id"]); _cleanup(root)
        session = SessionLocal()
        try: assert session.query(Company).filter(Company.id.in_(seen)).count() == 0
        finally: session.close()


if __name__ == "__main__": asyncio.run(main())
