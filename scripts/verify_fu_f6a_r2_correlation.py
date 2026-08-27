"""Resumable persisted fixture and R2-B idempotency proof for Decision provenance."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalizationService
from app.application.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReferenceService
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.models.actuals import ActualWeeklyObservation
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from time import perf_counter
from uuid_extensions import uuid7

MANIFEST = Path(__file__).with_name(".fu_f6a_r2_correlation.json")
R2C_MANIFEST = Path(__file__).with_name(".fu_f6a_r2_c_pre_assoc.json")
R2D_MANIFEST = Path(__file__).with_name(".fu_f6a_r2_d_post_assoc.json")
R2E_MANIFEST = Path(__file__).with_name(".fu_f6a_r2_e_partial.json")


def save(value): MANIFEST.write_text(json.dumps(value, sort_keys=True, indent=2), encoding="utf-8")
def load(): return json.loads(MANIFEST.read_text(encoding="utf-8"))


async def drive(execution_id, company_id):
    for _ in range(6):
        session = SessionLocal()
        try:
            if await BusinessWorkflowScheduler(session).run_next_ready(execution_id, company_id) is None: break
        finally: session.close()


def state(session, company_id, execution_id):
    refs = session.query(RuntimeResultReference).filter_by(execution_id=execution_id).order_by(RuntimeResultReference.result_type).all()
    tasks = session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order).all()
    return (session.query(RuntimeExecution).filter_by(execution_id=execution_id, company_id=company_id).one().state,
            tuple((x.task_id, x.state) for x in tasks),
            tuple((x.result_type, hashlib.sha256(json.dumps(x.inline_result, sort_keys=True, default=str).encode()).hexdigest()) for x in refs))


def counts(session, company_id, execution_id):
    snapshots = session.query(DecisionSnapshot).filter_by(company_id=company_id).count()
    candidates = session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count()
    associations = session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=company_id, execution_id=execution_id).count()
    return snapshots, candidates, associations


async def setup():
    assert not MANIFEST.exists(), "R2 fixture manifest already exists"
    session = SessionLocal(); company = user = None
    try:
        tag = "fu_f6a_r2_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.commit()
        payload = {"items": [{"sku_code": "SKU-R2", "demand_history": list(range(100, 132)), "lead_time_days": 7, "initial_stock": 500, "eoq": 100, "product_level": "finished_good"}]}
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
            dataset_hash=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), source_type=tag,
            encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True)
        session.add(dataset); session.commit()
        ActualWeeklyLedgerService().ingest_dataset_actuals(company.id, user.id, dataset.id,
            [{"material_code": "SKU-R2", "period": f"2026-W{week:02d}", "quantity": 100 + week, "product_level": "finished_good"} for week in range(1, 33)], "sales")
        started = perf_counter()
        accepted = BusinessWorkflowAcceptanceService().accept_or_resolve(company.id, user.id, dataset.id,
            request_metadata={"params": {"forecast_vintage": {"demand_type": "sales", "product_metadata": {"SKU-R2": {"product_level": "finished_good"}}}}})
        await drive(accepted.execution_id, company.id)
        analytics_ms = (perf_counter() - started) * 1000
        session.expire_all()
        finalization = session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=company.id, execution_id=accepted.execution_id).one()
        aggregate = session.query(RuntimeResultReference).filter_by(company_id=company.id, execution_id=accepted.execution_id, runtime_task_id=None, result_type="business_workflow").one()
        association = session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=company.id, execution_id=accepted.execution_id).one()
        snapshot = session.query(DecisionSnapshot).filter_by(id=association.decision_snapshot_id, company_id=company.id).one()
        assert finalization.status == "succeeded" and association.decision_finalization_id == finalization.id
        assert (association.material_code, association.demand_type, association.decision_context, association.decision_cutoff_period) == (snapshot.material_code, snapshot.demand_type, snapshot.decision_context, snapshot.decision_cutoff_period)
        save({"company_id": str(company.id), "user_id": str(user.id), "dataset_id": str(dataset.id), "execution_id": str(accepted.execution_id), "aggregate_result_reference_id": str(aggregate.id), "decision_finalization_id": str(finalization.id), "snapshot_id": str(snapshot.id), "association_id": str(association.id), "material_code": association.material_code, "demand_type": association.demand_type, "decision_context": association.decision_context, "cutoff_period": association.decision_cutoff_period, "analytics_ms": analytics_ms})
        session.close(); session = SessionLocal()
        manifest = load(); cid, eid = UUID(manifest["company_id"]), UUID(manifest["execution_id"])
        assert counts(session, cid, eid) == (1, session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == cid).count(), 1)
        assert state(session, cid, eid)[1] == (("forecast", "completed"), ("safety_stock", "completed"), ("simulation", "completed"), ("backtest", "completed"))
        print("FU_F6A_R2_BASE_FIXTURE_COMPLETE", manifest, flush=True)
    finally: session.close()


def retry():
    manifest = load(); cid, eid = UUID(manifest["company_id"]), UUID(manifest["execution_id"])
    session = SessionLocal()
    try:
        before_counts, before_state = counts(session, cid, eid), state(session, cid, eid)
        original_association = UUID(manifest["association_id"]); original_snapshot = UUID(manifest["snapshot_id"])
    finally: session.close()


def r2c_setup(manifest_path=R2C_MANIFEST, marker="FU_F6A_R2_C_FIXTURE_COMPLETE"):
    """Canonical RuntimeStore fixture using persisted base result payloads only."""
    from app.engine.runtime_store import RuntimeStore
    assert not manifest_path.exists(), "fixture manifest already exists"
    base = load(); cid = UUID(base["company_id"]); base_eid = UUID(base["execution_id"])
    session = SessionLocal()
    try:
        source = session.query(RuntimeExecution).filter_by(execution_id=base_eid, company_id=cid).one()
        source_tasks = session.query(RuntimeTask).filter_by(execution_id=base_eid).order_by(RuntimeTask.task_order).all()
        source_refs = {r.result_type: r for r in session.query(RuntimeResultReference).filter_by(execution_id=base_eid).filter(RuntimeResultReference.runtime_task_id.isnot(None)).all()}
        execution = RuntimeExecution(execution_id=uuid7(), company_id=cid, user_id=source.user_id, dataset_id=source.dataset_id,
            workflow_id=source.workflow_id, analysis_type="business_workflow", state="created", metadata_=source.metadata_)
        task_rows = [{"workflow_id": execution.workflow_id, "task_id": t.task_id, "capability": t.capability, "task_order": t.task_order,
            "required": t.required, "skippable": t.skippable, "dependencies": t.dependencies, "max_attempts": t.max_attempts, "retryable": t.retryable, "timeout_seconds": t.timeout_seconds} for t in source_tasks]
        store = RuntimeStore(session); store.create_execution(execution, task_rows); session.flush()
        execution = store.transition_execution(execution.execution_id, cid, "created", "queued", execution.row_version)
        execution = store.transition_execution(execution.execution_id, cid, "queued", "running", execution.row_version)
        for task in store.get_tasks(execution.execution_id, cid):
            claimed, _ = store.claim_task(execution.execution_id, task.task_id, cid, "fu_f6a_r2_fixture", 300, task.row_version)
            result_type = {"demand_forecast":"forecast"}.get(task.capability, task.task_id)
            store.complete_task_attempt(execution.execution_id, task.task_id, cid, claimed.lease_token, result_type, source_refs[result_type].inline_result, source_refs[result_type].result_version, source_refs[result_type].contract_version)
        session.flush(); execution = store.get_execution(execution.execution_id, cid); store.complete_execution(execution.execution_id, cid, execution.row_version); aggregate = store.aggregate_business_workflow(execution.execution_id, cid); session.commit()
        finalization_id = BusinessWorkflowDecisionFinalizationService().ensure(cid, execution.execution_id)
        manifest_path.write_text(json.dumps({"company_id":str(cid),"execution_id":str(execution.execution_id),"aggregate_id":str(aggregate.id),"finalization_id":str(finalization_id),"base_execution_id":str(base_eid)},indent=2),encoding="utf-8")
        session.close(); session=SessionLocal(); assert session.query(BusinessWorkflowDecisionFinalization).filter_by(id=finalization_id,status="pending").count()==1 and session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(execution_id=execution.execution_id).count()==0
        print(marker, {"execution_id":str(execution.execution_id),"aggregate_id":str(aggregate.id),"finalization_id":str(finalization_id)}, flush=True)
    finally: session.close()


def r2c_failure():
    m=json.loads(R2C_MANIFEST.read_text()); cid,eid=UUID(m["company_id"]),UUID(m["execution_id"])
    class FailBeforeAssociation:
        def ensure_for_plan(self,*args,**kwargs): raise RuntimeError("InjectedPreAssociationFailure")
    result=BusinessWorkflowDecisionFinalizationService(reference_service_factory=FailBeforeAssociation).finalize(cid,eid)
    s=SessionLocal()
    try:
        f=s.query(BusinessWorkflowDecisionFinalization).filter_by(id=UUID(m["finalization_id"])).one(); snaps=s.query(DecisionSnapshot).filter_by(company_id=cid,material_code="SKU-R2").all()
        assert result.status=="failed" and f.status=="failed" and len(snaps)>=1 and s.query(BusinessWorkflowDecisionSnapshotReference).filter_by(execution_id=eid).count()==0
        m["snapshot_id"]=str(snaps[-1].id); R2C_MANIFEST.write_text(json.dumps(m,indent=2),encoding="utf-8")
        print("FU_F6A_R2_C_FAILURE_STATE_VERIFIED", {"finalization_status":f.status,"attempt_count":f.attempt_count,"snapshot_id":m["snapshot_id"],"association_count":0},flush=True)
    finally:s.close()


def r2c_recover():
    m=json.loads(R2C_MANIFEST.read_text());cid,eid=UUID(m["company_id"]),UUID(m["execution_id"]);result=BusinessWorkflowDecisionFinalizationService().finalize(cid,eid);s=SessionLocal()
    try:
        refs=BusinessWorkflowDecisionSnapshotReferenceService().list_for_execution(cid,eid);assert result.status=="succeeded" and len(refs)==1 and str(refs[0].decision_snapshot_id)==m["snapshot_id"]
        print("FU_F6A_R2_C_PRE_ASSOC_RECOVERY_COMPLETE", {"snapshot_id":m["snapshot_id"],"association_id":str(refs[0].id)},flush=True)
    finally:s.close()

def r2d_setup(): r2c_setup(R2D_MANIFEST, "FU_F6A_R2_D_FIXTURE_COMPLETE")

def r2d_failure():
    m=json.loads(R2D_MANIFEST.read_text());cid,eid=UUID(m["company_id"]),UUID(m["execution_id"])
    class CrashBeforeSuccess(BusinessWorkflowDecisionFinalizationService):
        def _finish(self, claim, plan=None, error=None): raise RuntimeError("InjectedPostAssociationPreSuccessCrash")
    try: CrashBeforeSuccess(lease_seconds=-1).finalize(cid,eid)
    except RuntimeError as exc:
        assert str(exc)=="InjectedPostAssociationPreSuccessCrash"
    s=SessionLocal()
    try:
        f=s.query(BusinessWorkflowDecisionFinalization).filter_by(id=UUID(m["finalization_id"])).one();r=s.query(BusinessWorkflowDecisionSnapshotReference).filter_by(execution_id=eid).one();m.update({"snapshot_id":str(r.decision_snapshot_id),"association_id":str(r.id),"attempt_count":f.attempt_count});R2D_MANIFEST.write_text(json.dumps(m,indent=2),encoding="utf-8");assert f.status=="running" and r.id
        print("FU_F6A_R2_D_FAILURE_STATE_VERIFIED",{"status":f.status,"attempt_count":f.attempt_count,"association_id":str(r.id),"snapshot_id":str(r.decision_snapshot_id)},flush=True)
    finally:s.close()

def r2d_recover():
    m=json.loads(R2D_MANIFEST.read_text());cid,eid=UUID(m["company_id"]),UUID(m["execution_id"]);out=BusinessWorkflowDecisionFinalizationService().recover_due(cid);s=SessionLocal()
    try:
        f=s.query(BusinessWorkflowDecisionFinalization).filter_by(id=UUID(m["finalization_id"])).one();r=s.query(BusinessWorkflowDecisionSnapshotReference).filter_by(id=UUID(m["association_id"])).one();assert f.status=="succeeded" and str(r.decision_snapshot_id)==m["snapshot_id"];print("FU_F6A_R2_D_POST_ASSOC_RECOVERY_COMPLETE",{"status":f.status,"attempt_count":f.attempt_count,"association_id":str(r.id)},flush=True)
    finally:s.close()

async def r2e_setup():
    """The one authorized real two-SKU analytics fixture; Decision-only failure is patched."""
    from unittest.mock import patch
    import app.application.business_decision_plan as plan_module
    from scripts.verify_fu_f6a_r1_decision_finalization import create_dataset, completed_workflow, selective_policy_factory
    assert not R2E_MANIFEST.exists(), "R2-E manifest already exists"
    s=SessionLocal(); tag="fu_f6a_r2e_"+str(uuid7()).replace("-","")
    try:
        company=Company(id=uuid7(),name=tag,tax_id=tag);user=User(id=uuid7(),company_id=company.id,email=tag+"@x.invalid",hashed_password="x");s.add_all((company,user));s.commit()
        dataset_id=await create_dataset(company,user,["SKU-A","SKU-B"],tag)
        started=perf_counter();eid=await completed_workflow(company,user,dataset_id,["SKU-A","SKU-B"],patch.object(plan_module,"DecisionPolicy",selective_policy_factory()));elapsed=(perf_counter()-started)*1000
        s.expire_all();f=s.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=company.id,execution_id=eid).one();refs=s.query(BusinessWorkflowDecisionSnapshotReference).filter_by(execution_id=eid).order_by(BusinessWorkflowDecisionSnapshotReference.material_code).all();agg=s.query(RuntimeResultReference).filter_by(execution_id=eid,result_type="business_workflow",runtime_task_id=None).one();assert f.status=="partially_succeeded" and [r.material_code for r in refs]==["SKU-A"]
        R2E_MANIFEST.write_text(json.dumps({"company_id":str(company.id),"user_id":str(user.id),"dataset_id":str(dataset_id),"execution_id":str(eid),"aggregate_id":str(agg.id),"finalization_id":str(f.id),"sku_a_snapshot_id":str(refs[0].decision_snapshot_id),"sku_a_association_id":str(refs[0].id),"analytics_ms":elapsed},indent=2),encoding="utf-8")
        print("FU_F6A_R2_E_PARTIAL_STATE_VERIFIED",{"execution_id":str(eid),"status":f.status,"completed":f.completed_material_codes,"limitations":f.limitations,"sku_a_association":str(refs[0].id),"analytics_ms":round(elapsed,3)},flush=True)
    finally:s.close()

def r2e_recover():
    """Recover the interrupted partial checkpoint, then retry Decision work only."""
    eid=UUID("06a90a48-6d84-762e-8000-eb1568f56b7a");s=SessionLocal()
    try:
        e=s.query(RuntimeExecution).filter_by(execution_id=eid).one();f=s.query(BusinessWorkflowDecisionFinalization).filter_by(execution_id=eid).one();refs=s.query(BusinessWorkflowDecisionSnapshotReference).filter_by(execution_id=eid).all();a=next(x for x in refs if x.material_code=="SKU-A");cand=s.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=a.decision_snapshot_id).order_by(DecisionSnapshotCandidate.ordinal).all();results=s.query(RuntimeResultReference).filter_by(execution_id=eid).all()
        manifest={"company_id":str(e.company_id),"dataset_id":str(e.dataset_id),"execution_id":str(eid),"task_ids":[str(x.id) for x in s.query(RuntimeTask).filter_by(execution_id=eid).order_by(RuntimeTask.task_order)],"result_reference_ids":{x.result_type:str(x.id) for x in results},"aggregate_id":str(next(x.id for x in results if x.result_type=="business_workflow"),),"finalization_id":str(f.id),"partial_status":f.status,"partial_attempt_count":f.attempt_count,"completed_material_codes":f.completed_material_codes,"sku_a_snapshot_id":str(a.decision_snapshot_id),"sku_a_candidate_ids":[str(x.id) for x in cand],"sku_a_association_id":str(a.id),"sku_b_snapshot_id":None,"sku_b_association_id":None}
        R2E_MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        assert f.status=="partially_succeeded" and len(refs)==1
    finally:s.close()
    result=BusinessWorkflowDecisionFinalizationService().finalize(UUID(manifest["company_id"]),eid);s=SessionLocal()
    try:
        f=s.query(BusinessWorkflowDecisionFinalization).filter_by(id=UUID(manifest["finalization_id"])).one();refs=s.query(BusinessWorkflowDecisionSnapshotReference).filter_by(execution_id=eid).order_by(BusinessWorkflowDecisionSnapshotReference.material_code).all();by={x.material_code:x for x in refs};assert f.status=="succeeded" and len(refs)==2 and str(by["SKU-A"].id)==manifest["sku_a_association_id"] and str(by["SKU-A"].decision_snapshot_id)==manifest["sku_a_snapshot_id"]
        manifest.update({"final_status":f.status,"final_attempt_count":f.attempt_count,"sku_b_snapshot_id":str(by["SKU-B"].decision_snapshot_id),"sku_b_association_id":str(by["SKU-B"].id),"recovery":"complete"});R2E_MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        print("FU_F6A_R2_E_PARTIAL_COMPLETE",{"finalization":f.status,"attempt_count":f.attempt_count,"sku_a_association":manifest["sku_a_association_id"],"sku_b_association":manifest["sku_b_association_id"]},flush=True)
    finally:s.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "setup": asyncio.run(setup())
    elif mode == "retry": retry()
    elif mode == "r2c-setup": r2c_setup()
    elif mode == "r2c-failure": r2c_failure()
    elif mode == "r2c-recover": r2c_recover()
    elif mode == "r2d-setup": r2d_setup()
    elif mode == "r2d-failure": r2d_failure()
    elif mode == "r2d-recover": r2d_recover()
    elif mode == "r2e-setup": asyncio.run(r2e_setup())
    elif mode == "r2e-recover": r2e_recover()
    else: raise ValueError("use setup or retry")
