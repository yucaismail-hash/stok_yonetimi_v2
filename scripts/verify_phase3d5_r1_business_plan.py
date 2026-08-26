"""One real completed Business Workflow -> derived Decision-plan proof."""
import asyncio, hashlib, json
from pathlib import Path
import sys
from time import perf_counter
from uuid_extensions import uuid7
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
from app.models.security import CompanyEncryptionKey
from app.models.decision_snapshot import DecisionSnapshot,DecisionSnapshotCandidate
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.services.security import EncryptionService
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.business_decision_plan import BusinessDecisionPlanService
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler

async def main():
 s=SessionLocal(); c=u=d=None; started=perf_counter()
 try:
  tag='d5_r1_'+str(uuid7()).replace('-','');c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();payload={'items':[{'sku_code':'SKU','demand_history':list(range(100,132)),'lead_time_days':7,'initial_stock':500,'eoq':100,'product_level':'finished_good'}]};d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256((tag+json.dumps(payload)).encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,payload),is_active=True);s.add(d);s.commit();setup=perf_counter()
  ActualWeeklyLedgerService().ingest_dataset_actuals(c.id,u.id,d.id,[{'material_code':'SKU','period':f'2026-W{i:02d}','quantity':100+i,'product_level':'finished_good'} for i in range(1,33)],'sales')
  accepted=BusinessWorkflowAcceptanceService().accept_or_resolve(c.id,u.id,d.id,request_metadata={'params':{'forecast_vintage':{'demand_type':'sales','product_metadata':{'SKU':{'product_level':'finished_good'}}}}})
  for _ in range(5):
   s.close();s=SessionLocal();out=await BusinessWorkflowScheduler(s).run_next_ready(accepted.execution_id,c.id)
   if out is None:break
  s.expire_all();e=s.query(RuntimeExecution).filter_by(execution_id=accepted.execution_id).one();tasks=s.query(RuntimeTask).filter_by(execution_id=e.execution_id).order_by(RuntimeTask.task_order).all();assert e.state=='completed' and float(e.progress)==100 and [x.task_id for x in tasks]==['forecast','safety_stock','simulation','backtest'] and all(x.state=='completed' for x in tasks);cutoff=e.metadata_['request_metadata']['params']['forecast_cutoff_period'];before=(len(tasks),s.query(RuntimeResultReference).filter_by(execution_id=e.execution_id).count(),s.query(ForecastVintage).filter_by(company_id=c.id).count());analytics=perf_counter()
  plan_start=perf_counter();plan=BusinessDecisionPlanService().materialize(c.id,e.execution_id);plan_end=perf_counter();again=BusinessDecisionPlanService().materialize(c.id,e.execution_id);assert plan==again and plan.materials_total==1 and len(plan.items)==1 and not plan.limitations;item=plan.items[0];snap=s.query(DecisionSnapshot).filter_by(id=item['decision_snapshot_id'],company_id=c.id).one();assert (snap.material_code,snap.demand_type,snap.decision_context,snap.decision_cutoff_period)==('SKU','sales','REPLENISHMENT',cutoff) and s.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snap.id).count()==item['candidate_count'];after=(len(s.query(RuntimeTask).filter_by(execution_id=e.execution_id).all()),s.query(RuntimeResultReference).filter_by(execution_id=e.execution_id).count(),s.query(ForecastVintage).filter_by(company_id=c.id).count());assert before==after;fresh=BusinessDecisionPlanService().materialize(c.id,e.execution_id);assert fresh==plan;print('PHASE 3D5 R1 PASS',{'execution_id':str(e.execution_id),'cutoff':cutoff,'tasks':[x.task_id for x in tasks],'snapshot_id':item['decision_snapshot_id'],'setup_ms':round((setup-started)*1000,3),'analytics_ms':round((analytics-setup)*1000,3),'plan_ms':round((plan_end-plan_start)*1000,3),'items':plan.materials_total},flush=True)
 finally:
  if s:
   s.rollback()
   if c:
    eids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=c.id).all()]; vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=c.id).all()]; sids=[x[0] for x in s.query(DecisionSnapshot.id).filter_by(company_id=c.id).all()];s.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(sids)).delete(synchronize_session=False);s.query(DecisionSnapshot).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(eids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(eids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(eids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(eids)).delete(synchronize_session=False);s.query(ActualWeeklyRevision).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(Dataset).filter_by(id=d.id).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=u.id).delete(synchronize_session=False);s.query(User).filter_by(id=u.id).delete(synchronize_session=False);s.query(Company).filter_by(id=c.id).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':asyncio.run(main())
