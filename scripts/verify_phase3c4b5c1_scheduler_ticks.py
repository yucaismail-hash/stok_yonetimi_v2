"""PostgreSQL ownership/idempotency proof for callable scheduler ticks."""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

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
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape


class _FailingScanner:
    def __init__(self, *args, **kwargs): pass
    def scan_and_activate(self, *args, **kwargs): raise RuntimeError("PROBE_TICK_FAILURE")


def _cleanup(root):
    s=SessionLocal()
    try:
        cid=root["company_id"]; ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid,analysis_type="retraining")]
        s.query(RetrainingSchedulerTick).filter_by(company_id=cid).delete(synchronize_session=False)
        s.query(RetrainingResourceLease).filter_by(company_id=cid).delete(synchronize_session=False)
        s.query(RetrainingJob).filter_by(company_id=cid).delete(synchronize_session=False)
        if ids:
            tids=[x[0] for x in s.query(RuntimeTask.id).filter(RuntimeTask.execution_id.in_(ids))]
            if tids:
                s.query(RuntimeResultReference).filter(RuntimeResultReference.runtime_task_id.in_(tids)).delete(synchronize_session=False)
                s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.runtime_task_id.in_(tids)).delete(synchronize_session=False)
            s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False)
            s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False)
            s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
        s.commit(); cleanup_fixture(s,type("Ids",(),root)())
    finally:s.close()


async def main():
    roots=[]; original=xgboost.XGBRegressor.fit; fits={"count":0}
    xgboost.XGBRegressor.fit=lambda *a,**kw:(fits.__setitem__("count",fits["count"]+1),original(*a,**kw))[1]
    try:
        root=await create_tier_shape("tier3",8,"TICK","sales"); roots.append(root)
        at=datetime(2026,8,12,10,0,7,tzinfo=timezone.utc)
        service=RetrainingScannerSchedulerService(capacity=1,lease_seconds=60)
        # A/B: the first configured bucket executes one B5B cycle; duplicate
        # delivery reads the durable completed tick, with no duplicate runtime.
        first=service.run_tick(root["company_id"],root["start_period"],root["end_period"],scheduled_for=at,cadence_seconds=60,owner_id="owner-a")
        assert first.status=="COMPLETED" and len(first.activation_report.activated)==1
        second=RetrainingScannerSchedulerService(capacity=1).run_tick(root["company_id"],root["start_period"],root["end_period"],scheduled_for=at+timedelta(seconds=20),cadence_seconds=60,owner_id="owner-b")
        assert second.status=="ALREADY_COMPLETED" and second.tick_id==first.tick_id
        s=SessionLocal()
        try:
            assert s.query(RetrainingSchedulerTick).filter_by(company_id=root["company_id"]).count()==1
            assert s.query(RetrainingJob).filter_by(company_id=root["company_id"]).count()==1
            assert s.query(RuntimeExecution).filter_by(company_id=root["company_id"],analysis_type="retraining").count()==1
            assert s.query(RuntimeTask).filter_by(company_id=root["company_id"]).count()==1
        finally:s.close()

        # C: two independent process-equivalent callers converge to one bucket.
        next_at=at+timedelta(minutes=1)
        def concurrent(owner):
            return RetrainingScannerSchedulerService(capacity=1).run_tick(root["company_id"],root["start_period"],root["end_period"],scheduled_for=next_at,cadence_seconds=60,owner_id=owner)
        with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(concurrent,("race-a","race-b")))
        assert sum(x.status=="COMPLETED" for x in outcomes)==1
        assert sum(x.status in ("ALREADY_RUNNING","ALREADY_COMPLETED") for x in outcomes)==1

        # D/F: next cadence bucket is durable across fresh service construction;
        # missed downtime does not replay arbitrary earlier buckets.
        future=RetrainingScannerSchedulerService(capacity=1).run_tick(root["company_id"],root["start_period"],root["end_period"],scheduled_for=at+timedelta(minutes=5),cadence_seconds=60,owner_id="restart")
        assert future.status=="COMPLETED"
        s=SessionLocal()
        try:
            ticks=s.query(RetrainingSchedulerTick).filter_by(company_id=root["company_id"]).order_by(RetrainingSchedulerTick.scheduled_bucket_at).all()
            assert len(ticks)==3 and [x.state for x in ticks]==["completed"]*3
            # Fresh session reconstruction from durable tick and runtime IDs.
            reloaded=s.query(RetrainingSchedulerTick).filter_by(id=first.tick_id,company_id=root["company_id"]).one()
            assert reloaded.tick_identity==first.tick_identity and reloaded.report_summary["activated"]==1
        finally:s.close()

        # E: a failed bucket stays audited/no immediate retry; next bucket works.
        failed_at=at+timedelta(minutes=10)
        s=SessionLocal()
        try:
            before_failed_counts=(s.query(RetrainingJob).filter_by(company_id=root["company_id"]).count(),
                                  s.query(RuntimeExecution).filter_by(company_id=root["company_id"],analysis_type="retraining").count())
        finally:s.close()
        failed=RetrainingScannerSchedulerService(scanner_factory=_FailingScanner).run_tick(root["company_id"],root["start_period"],root["end_period"],scheduled_for=failed_at,cadence_seconds=60,owner_id="fail")
        assert failed.status=="FAILED"
        assert RetrainingScannerSchedulerService().run_tick(root["company_id"],root["start_period"],root["end_period"],scheduled_for=failed_at,cadence_seconds=60,owner_id="retry").status=="FAILED_PREVIOUSLY"
        s=SessionLocal()
        try:
            assert (s.query(RetrainingJob).filter_by(company_id=root["company_id"]).count(),
                    s.query(RuntimeExecution).filter_by(company_id=root["company_id"],analysis_type="retraining").count()) == before_failed_counts
        finally:s.close()
        later=RetrainingScannerSchedulerService(capacity=1).run_tick(root["company_id"],root["start_period"],root["end_period"],scheduled_for=failed_at+timedelta(minutes=1),cadence_seconds=60,owner_id="after-fail")
        assert later.status=="COMPLETED"

        # H/I/J: company isolation and zero governance/model execution: C1 starts
        # runtimes only through B5B; no worker fit/artifact/governance is invoked.
        other=await create_tier_shape("tier3",8,"OTHER","sales"); roots.append(other)
        isolated=RetrainingScannerSchedulerService(capacity=1).run_tick(other["company_id"],other["start_period"],other["end_period"],scheduled_for=at,cadence_seconds=60,owner_id="other")
        assert isolated.status=="COMPLETED" and isolated.tick_id!=first.tick_id
        s=SessionLocal()
        try:
            assert s.query(RetrainingSchedulerTick).filter_by(company_id=root["company_id"]).count()==5
            assert s.query(RetrainingSchedulerTick).filter_by(company_id=other["company_id"]).count()==1
            assert s.query(ModelArtifact).filter_by(company_id=root["company_id"]).count()==0 and fits["count"]==0
            assert s.query(ChampionChallengerDecision).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(ChampionRegistryEntry).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(ChampionRegistryCurrent).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(ChampionRegistryTransition).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(CompanyLearningMemory).filter_by(company_id=root["company_id"]).count()==0
            assert s.query(UserLearningData).filter_by(company_id=root["company_id"]).count()==0
        finally:s.close()
        print("PHASE3C4B5C1 PASS",{"first":first.status,"concurrent":[x.status for x in outcomes],"future":future.status,"failed":failed.status,"fits":fits["count"]})
    finally:
        xgboost.XGBRegressor.fit=original
        seen=set()
        for root in roots:
            if root["company_id"] not in seen: seen.add(root["company_id"]); _cleanup(root)
        s=SessionLocal()
        try: assert s.query(Company).filter(Company.id.in_(seen)).count()==0
        finally:s.close()


if __name__=="__main__": asyncio.run(main())
