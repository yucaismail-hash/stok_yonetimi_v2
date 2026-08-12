"""PostgreSQL proof for explicit retraining cooldown, priority, and capacity."""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.retraining_admission import RetrainingAdmissionService, RetrainingResourceLeaseError
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_execution import RetrainingExecutionService, RetrainingTrainingWorker
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.retraining_resource_lease import RetrainingResourceLease
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
    result = RetrainingJobService().accept_candidate(RetrainingJobRequest(
        fixture["company_id"], fixture["material_code"], fixture["demand_type"], fixture["start_period"],
        fixture["end_period"], f"2026-W{int(fixture['end_period'][-2:]) - len(range(8)):02d}", _eligibility(fixture),
    ))
    assert result.status == "CREATED"
    return result.job_id


def _expire_resource(company_id, job_id):
    session = SessionLocal()
    try:
        lease = session.query(RetrainingResourceLease).filter_by(
            company_id=company_id, retraining_job_id=job_id, active=True,
        ).one()
        lease.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()
        return lease.lease_token
    finally:
        session.close()


def _release_all(company_id):
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        session.query(RetrainingResourceLease).filter_by(company_id=company_id, active=True).update(
            {"active": False, "released_at": now, "release_reason_code": "PROBE_RELEASE"}, synchronize_session=False,
        )
        session.commit()
    finally:
        session.close()


def _cleanup(root):
    session = SessionLocal()
    try:
        company_id = root["company_id"]
        artifacts = session.query(ModelArtifact).filter_by(company_id=company_id).all()
        execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(
            company_id=company_id, analysis_type="retraining",
        )]
        session.query(RetrainingResourceLease).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(RetrainingJob).filter_by(company_id=company_id).delete(synchronize_session=False)
        for artifact in artifacts:
            LocalModelArtifactStorage().delete_for_controlled_cleanup(artifact.artifact_storage_reference)
        session.query(ModelArtifact).filter_by(company_id=company_id).delete(synchronize_session=False)
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
    original_fit = xgboost.XGBRegressor.fit
    fits = {"count": 0}
    xgboost.XGBRegressor.fit = lambda *args, **kwargs: (fits.__setitem__("count", fits["count"] + 1), original_fit(*args, **kwargs))[1]
    root = None
    try:
        root = await create_tier_shape("tier3", 8, "COOL", "sales")
        context = {key: root[key] for key in ("company_id", "user_id", "dataset_id")}

        # A: first candidate is immediately eligible, explicitly starts, and trains.
        first_job = _job(root)
        first_start = RetrainingExecutionService(cooldown_seconds=120, capacity=2).start(root["company_id"], first_job)
        assert first_start.status == "STARTED"
        assert RetrainingTrainingWorker(worker_id="first", capacity=2).run(root["company_id"], first_job).status == "TRAINED"

        # B/C/D: new canonical evidence for the same scope is retained but cooled;
        # exact same candidate becomes eligible after a synthetic policy clock expiry.
        cooled_fixture = await create_tier_shape("tier3", 8, "COOL", "sales", context=context, cutoff_week=32, target_start_week=33)
        cooled_job = _job(cooled_fixture)
        cooled = RetrainingAdmissionService(cooldown_seconds=120, capacity=2).evaluate(root["company_id"], cooled_job)
        assert cooled.status == "COOLDOWN" and cooled.cooldown_until is not None
        # Independent PostgreSQL sessions serialize the durable decision for one
        # job; they do not create a second candidate or divergent cooldown state.
        with ThreadPoolExecutor(max_workers=2) as pool:
            concurrent_cooldown = list(pool.map(
                lambda _: RetrainingAdmissionService(cooldown_seconds=120, capacity=2).evaluate(root["company_id"], cooled_job).status,
                range(2),
            ))
        assert concurrent_cooldown == ["COOLDOWN", "COOLDOWN"]
        before_cooldown_fit = fits["count"]
        assert RetrainingExecutionService(cooldown_seconds=120, capacity=2).start(root["company_id"], cooled_job).status == "COOLDOWN"
        assert fits["count"] == before_cooldown_fit
        future = cooled.cooldown_until + timedelta(seconds=1)
        expired = RetrainingAdmissionService(cooldown_seconds=120, capacity=2, now_factory=lambda: future).evaluate(root["company_id"], cooled_job)
        assert expired.status == "ELIGIBLE_NOW"
        assert RetrainingJobService().accept_candidate(RetrainingJobRequest(
            cooled_fixture["company_id"], cooled_fixture["material_code"], cooled_fixture["demand_type"], cooled_fixture["start_period"], cooled_fixture["end_period"], "2026-W32", _eligibility(cooled_fixture),
        )).status == "ALREADY_EXISTS"

        # E/F/I: caller-provided queue ordering is deterministic; capacity admits
        # the highest evidence score and leaves lower priority jobs pending.
        priority_fixtures = [await create_tier_shape("tier3", 8, code, "sales", context=context)
                             for code in ("PRIO_LOW", "PRIO_MID", "PRIO_HIGH")]
        priority_jobs = [_job(fixture) for fixture in priority_fixtures]
        session = SessionLocal()
        try:
            for job_id, sample in zip(priority_jobs, (10, 20, 30)):
                session.query(RetrainingJob).filter_by(id=job_id).update({"sample_count": sample})
            session.commit()
        finally:
            session.close()
        priority = RetrainingAdmissionService(capacity=1)
        ranked = priority.ranked(root["company_id"], priority_jobs)
        assert [row.job_id for row in ranked] == [priority_jobs[2], priority_jobs[1], priority_jobs[0]]
        winner = priority.admit(root["company_id"], ranked[0].job_id, "priority-winner")
        assert winner.status == "ADMITTED"
        blocked = priority.admit(root["company_id"], ranked[1].job_id, "priority-loser")
        assert blocked.status == "CAPACITY_BLOCKED"
        priority.release(root["company_id"], winner.job_id, winner.resource_lease_token, "PROBE_TERMINAL")
        assert priority.admit(root["company_id"], ranked[1].job_id, "priority-next").status == "ADMITTED"
        _release_all(root["company_id"])

        # G/H: three independent sessions contend for capacity two; a duplicate
        # job admission resolves to its existing single active lease.
        contenders = [await create_tier_shape("tier3", 8, code, "sales", context=context)
                      for code in ("RACE_A", "RACE_B", "RACE_C")]
        contender_jobs = [_job(fixture) for fixture in contenders]
        def admit(job_id):
            return RetrainingAdmissionService(capacity=2).admit(root["company_id"], job_id, f"worker-{job_id}")
        with ThreadPoolExecutor(max_workers=3) as pool:
            admissions = list(pool.map(admit, contender_jobs))
        assert sum(row.status == "ADMITTED" for row in admissions) == 2
        assert sum(row.status == "CAPACITY_BLOCKED" for row in admissions) == 1
        admitted = next(row for row in admissions if row.status == "ADMITTED")
        duplicate = RetrainingAdmissionService(capacity=2).admit(root["company_id"], admitted.job_id, "duplicate")
        assert duplicate.status == "ADMITTED" and duplicate.resource_lease_token == admitted.resource_lease_token

        # J/K: heartbeat owns the current token; expiration permits re-admission,
        # while the old owner cannot mutate the newer lease.
        heartbeat_service = RetrainingAdmissionService(capacity=2, lease_seconds=30)
        heartbeat_service.heartbeat(root["company_id"], admitted.job_id, admitted.resource_lease_token)
        old_token = _expire_resource(root["company_id"], admitted.job_id)
        reclaimed = RetrainingAdmissionService(capacity=2).admit(root["company_id"], admitted.job_id, "reclaimer")
        assert reclaimed.status == "ADMITTED" and reclaimed.resource_lease_token != old_token
        for operation in ("heartbeat", "release"):
            try:
                getattr(RetrainingAdmissionService(capacity=2), operation)(root["company_id"], admitted.job_id, old_token)
                raise AssertionError("stale resource owner accepted")
            except RetrainingResourceLeaseError:
                pass
        _release_all(root["company_id"])

        # L/M/O/P/Q: terminal worker release, tenant isolation, persisted reload,
        # and zero governance state all remain independent of the retraining lane.
        release_fixture = await create_tier_shape("tier3", 8, "RELEASE", "sales", context=context)
        release_job = _job(release_fixture)
        assert RetrainingExecutionService(capacity=1).start(root["company_id"], release_job).status == "STARTED"
        assert RetrainingTrainingWorker(worker_id="release", capacity=1).run(root["company_id"], release_job).status == "TRAINED"
        session = SessionLocal()
        try:
            assert session.query(RetrainingResourceLease).filter_by(retraining_job_id=release_job, active=True).count() == 0
            persisted = session.query(RetrainingJob).filter_by(id=cooled_job, company_id=root["company_id"]).one()
            assert persisted.cooldown_policy_version == "retraining_cooldown_v1"
            assert persisted.priority_policy_version == "retraining_priority_v1"
            assert persisted.admission_result in ("COOLDOWN", "ELIGIBLE_NOW")
            assert session.query(ChampionChallengerDecision).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(ChampionRegistryEntry).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(ChampionRegistryCurrent).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(ChampionRegistryTransition).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(CompanyLearningMemory).filter_by(company_id=root["company_id"]).count() == 0
            assert session.query(UserLearningData).filter_by(company_id=root["company_id"]).count() == 0
        finally:
            session.close()
        other = await create_tier_shape("tier3", 8, "OTHER", "sales")
        other_job = _job(other)
        assert RetrainingAdmissionService(capacity=1).admit(other["company_id"], other_job, "other-company").status == "ADMITTED"
        _cleanup(other)
        print("PHASE3C4B4 PASS", {"fits": fits["count"], "cooldown": "COOLDOWN", "priority": [str(row.job_id) for row in ranked], "capacity": [row.status for row in admissions], "reclaim": "ADMITTED"})
    finally:
        xgboost.XGBRegressor.fit = original_fit
        if root is not None:
            _cleanup(root)
            session = SessionLocal()
            try:
                assert session.query(Company).filter_by(id=root["company_id"]).count() == 0
            finally:
                session.close()


if __name__ == "__main__":
    asyncio.run(main())
