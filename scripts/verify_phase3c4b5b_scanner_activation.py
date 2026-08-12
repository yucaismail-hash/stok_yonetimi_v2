"""PostgreSQL proof for explicit scanner-to-admission-to-runtime activation."""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.retraining_execution import RetrainingTrainingWorker
from app.application.retraining_execution import RetrainingExecutionService
from app.application.retraining_scanner import RetrainingScannerService
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


def _counts(company_id):
    s = SessionLocal()
    try:
        return {"jobs": s.query(RetrainingJob).filter_by(company_id=company_id).count(),
                "leases": s.query(RetrainingResourceLease).filter_by(company_id=company_id).count(),
                "active_leases": s.query(RetrainingResourceLease).filter_by(company_id=company_id, active=True).count(),
                "executions": s.query(RuntimeExecution).filter_by(company_id=company_id, analysis_type="retraining").count(),
                "tasks": s.query(RuntimeTask).filter_by(company_id=company_id).count(),
                "attempts": s.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
                "results": s.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
                "artifacts": s.query(ModelArtifact).filter_by(company_id=company_id).count()}
    finally: s.close()


def _cleanup(root):
    s = SessionLocal()
    try:
        cid = root["company_id"]
        artifacts = s.query(ModelArtifact).filter_by(company_id=cid).all()
        ids = [x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid, analysis_type="retraining")]
        s.query(RetrainingResourceLease).filter_by(company_id=cid).delete(synchronize_session=False)
        s.query(RetrainingJob).filter_by(company_id=cid).delete(synchronize_session=False)
        for a in artifacts: LocalModelArtifactStorage().delete_for_controlled_cleanup(a.artifact_storage_reference)
        s.query(ModelArtifact).filter_by(company_id=cid).delete(synchronize_session=False)
        if ids:
            tids=[x[0] for x in s.query(RuntimeTask.id).filter(RuntimeTask.execution_id.in_(ids))]
            if tids:
                s.query(RuntimeResultReference).filter(RuntimeResultReference.runtime_task_id.in_(tids)).delete(synchronize_session=False)
                s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.runtime_task_id.in_(tids)).delete(synchronize_session=False)
            s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False)
            s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False)
            s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
        s.commit(); cleanup_fixture(s, type("Ids", (), root)())
    finally: s.close()


class _OneScopeStartFailure:
    """Probe-only activation failure; the next ranked scope must continue."""
    def __init__(self, session_factory, **kwargs):
        self._session_factory, self._kwargs = session_factory, kwargs
    def start(self, company_id, job_id, worker_id):
        s = self._session_factory()
        try:
            material = s.query(RetrainingJob).filter_by(id=job_id, company_id=company_id).one().material_code
        finally: s.close()
        if material == "FAIL": raise ValueError("PROBE_ACTIVATION_FAILURE")
        return RetrainingExecutionService(self._session_factory, **self._kwargs).start(company_id, job_id, worker_id)


async def main():
    roots=[]; original=xgboost.XGBRegressor.fit; fits={"count":0}
    xgboost.XGBRegressor.fit=lambda *a,**kw:(fits.__setitem__("count",fits["count"]+1),original(*a,**kw))[1]
    try:
        # A/B/I/J: pure discovery is runtime/lease-free; explicit activation starts
        # one runtime/task, and only the worker later performs the one fit/artifact.
        root=await create_tier_shape("tier3",8,"ACT","sales"); roots.append(root)
        scanner=RetrainingScannerService(capacity=1)
        before=_counts(root["company_id"])
        discovery=scanner.scan(root["company_id"],root["start_period"],root["end_period"])
        assert _counts(root["company_id"])["executions"]==before["executions"] and _counts(root["company_id"])["leases"]==before["leases"]
        activated=scanner.scan_and_activate(root["company_id"],root["start_period"],root["end_period"],worker_id="activate")
        assert [x.admission_status for x in activated.activated]==["STARTED"]
        started=activated.activated[0]
        repeat=scanner.scan_and_activate(root["company_id"],root["start_period"],root["end_period"],worker_id="again")
        assert repeat.activated[0].admission_status=="ALREADY_STARTED" and _counts(root["company_id"])["executions"]==1
        trained=RetrainingTrainingWorker(worker_id="worker",capacity=1).run(root["company_id"],started.job_id)
        assert trained.status=="TRAINED" and fits["count"]==1
        s=SessionLocal()
        try:
            job=s.query(RetrainingJob).filter_by(id=started.job_id).one(); assert job.state=="trained" and job.model_artifact_id==trained.artifact_id
            assert s.query(RetrainingResourceLease).filter_by(retraining_job_id=job.id,active=True).count()==0
            # Fresh session primitive reconstruction.
            execution=s.query(RuntimeExecution).filter_by(execution_id=job.runtime_execution_id).one()
            assert execution.analysis_type=="retraining" and s.query(RuntimeTask).filter_by(execution_id=execution.execution_id).count()==1
        finally: s.close()

        # C/F/L: cooled high-priority job is deferred and consumes no slot; next
        # eligible job starts in capacity one.  A controlled invalid scope error
        # remains isolated in the report rather than corrupting the valid job.
        cool=await create_tier_shape("tier3",8,"COOL","sales"); roots.append(cool)
        cctx={k:cool[k] for k in ("company_id","user_id","dataset_id")}
        # Establish prior successful training via the existing explicit bridge.
        base=RetrainingScannerService(capacity=2).scan_and_activate(cool["company_id"],cool["start_period"],cool["end_period"])
        assert RetrainingTrainingWorker(worker_id="base",capacity=2).run(cool["company_id"],base.activated[0].job_id).status=="TRAINED"
        cooled=await create_tier_shape("tier3",8,"COOL","sales",context=cctx,cutoff_week=32,target_start_week=33)
        next_job=await create_tier_shape("tier3",8,"NEXT","sales",context=cctx)
        mixed=RetrainingScannerService(cooldown_seconds=600,capacity=1).scan_and_activate(cool["company_id"],"2026-W25","2026-W40")
        by_material={row.material_code:row for row in mixed.activated}
        assert by_material["COOL"].admission_status=="COOLDOWN"
        assert by_material["NEXT"].admission_status=="STARTED"
        s=SessionLocal()
        try:
            cool_job=s.query(RetrainingJob).filter_by(id=by_material["COOL"].job_id).one()
            assert cool_job.runtime_execution_id is None
            assert s.query(RetrainingResourceLease).filter_by(retraining_job_id=cool_job.id).count()==0
            # NEXT intentionally remains queued to prove cooldown does not take
            # capacity. Release this probe-owned slot before the independent
            # global-capacity race below.
            s.query(RetrainingResourceLease).filter_by(company_id=cool["company_id"], active=True).update(
                {"active": False, "released_at": datetime.now(timezone.utc), "release_reason_code": "PROBE_MATRIX_BOUNDARY"},
                synchronize_session=False,
            )
            s.commit()
        finally: s.close()

        # E/K: three candidates, capacity two, priority determines the admitted
        # pair; concurrent activation cannot duplicate runtime/task identity.
        race=await create_tier_shape("tier3",8,"RACE_A","sales"); roots.append(race)
        rctx={k:race[k] for k in ("company_id","user_id","dataset_id")}
        await create_tier_shape("tier3",8,"RACE_B","sales",context=rctx)
        await create_tier_shape("tier3",8,"RACE_C","sales",context=rctx)
        def activate(_): return RetrainingScannerService(capacity=2).scan_and_activate(race["company_id"],race["start_period"],race["end_period"],worker_id="race")
        with ThreadPoolExecutor(max_workers=2) as pool: reports=list(pool.map(activate,range(2)))
        s=SessionLocal()
        try:
            jobs=s.query(RetrainingJob).filter_by(company_id=race["company_id"]).all()
            assert len(jobs)==3 and sum(j.runtime_execution_id is not None for j in jobs)==2
            assert s.query(RuntimeTask).filter_by(company_id=race["company_id"]).count()==2
            s.query(RetrainingResourceLease).filter_by(company_id=race["company_id"], active=True).update(
                {"active": False, "released_at": datetime.now(timezone.utc), "release_reason_code": "PROBE_MATRIX_BOUNDARY"},
                synchronize_session=False,
            )
            s.commit()
        finally: s.close()

        # O: an isolated activation failure is reported while the next candidate
        # remains eligible to start under the same explicit invocation.
        failure=await create_tier_shape("tier3",8,"FAIL","sales"); roots.append(failure)
        fctx={k:failure[k] for k in ("company_id","user_id","dataset_id")}
        await create_tier_shape("tier3",8,"SURVIVE","sales",context=fctx)
        isolated=RetrainingScannerService(execution_service_factory=_OneScopeStartFailure,capacity=2).scan_and_activate(
            failure["company_id"],failure["start_period"],failure["end_period"],worker_id="isolation",
        )
        assert len(isolated.errors)==1 and isolated.errors[0].material_code=="FAIL"
        assert any(row.material_code=="SURVIVE" and row.admission_status=="STARTED" for row in isolated.activated)

        # N/Q: activation never invokes governance and remains unrelated to the
        # Business guard; B5B creates no timer or background process.
        s=SessionLocal()
        try:
            assert s.query(ChampionChallengerDecision).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(ChampionRegistryEntry).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(ChampionRegistryCurrent).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(ChampionRegistryTransition).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(CompanyLearningMemory).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(UserLearningData).filter_by(company_id=root["company_id"]).count()==0
        finally: s.close()
        print("PHASE3C4B5B PASS",{"fits":fits["count"],"first":started.runtime_execution_id,"cooled":by_material["COOL"].admission_status,"next":by_material["NEXT"].admission_status,"race_runtimes":2})
    finally:
        xgboost.XGBRegressor.fit=original
        seen=set()
        for root in roots:
            if root["company_id"] not in seen: seen.add(root["company_id"]); _cleanup(root)
        s=SessionLocal()
        try: assert s.query(Company).filter(Company.id.in_(seen)).count()==0
        finally: s.close()


if __name__=="__main__": asyncio.run(main())
