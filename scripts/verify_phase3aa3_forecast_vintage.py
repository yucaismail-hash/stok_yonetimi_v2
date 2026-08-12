"""PostgreSQL proof for immutable Forecast Vintage projection and target periods."""
import asyncio, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.forecast_vintage_service import ForecastVintageService, canonical_targets
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.engine.local_forecast_runner import LocalForecastRunner
from app.engine.runtime_store import RuntimeStore
from app.models.company import Company, User
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.dataset import Dataset
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService

def context(cutoff): return {'forecast_vintage': {'input_cutoff_period':cutoff,'demand_type':'sales','product_metadata':{'A':{'product_level':'finished_good','product_group':'G','product_class':'C'}}}}
async def main():
 s=SessionLocal(); c=u=d=None; p='phase3aa3_'+str(uuid7()).replace('-','')
 try:
  c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();cid=c.id;uid=u.id;hist=[3,5,2,6,4,7,3,8,4,9,5,10,6,11,7,12,8,13];data={'items':[{'sku_code':'A','demand_history':hist,'lead_time_days':14,'initial_stock':20,'eoq':5}]};d=Dataset(id=uuid7(),company_id=cid,user_id=uid,uploaded_by=uid,dataset_hash=hashlib.sha256((p+json.dumps(data)).encode()).hexdigest(),source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(uid,data),is_active=True);did=d.id;s.add(d);s.commit();ledger=ActualWeeklyLedgerService();ledger.ingest_dataset_actuals(cid,uid,did,[{'material_code':'A','period':f'2026-W{week:02d}','quantity':100+week,'product_level':'finished_good','product_group':'G','product_class':'C'} for week in range(1,33)],'sales')
  # Standalone Forecast Vintage A: explicit W32 cutoff and W33-W36 target identity.
  standalone=await WorkflowDispatcher().dispatch_single_analysis(cid,uid,did,'forecast',params={**context('2026-W32'),'horizon':4}); eid_a=standalone['execution_id'];await LocalForecastRunner().run(eid_a)
  # New accepted evidence advances the canonical current cutoff for Business Vintage B.
  ledger.ingest_dataset_actuals(cid,uid,did,[{'material_code':'A','period':f'2026-W{week:02d}','quantity':100+week,'product_level':'finished_good','product_group':'G','product_class':'C'} for week in range(33,36)],'sales')
  # Business Forecast Vintage B: explicit W35 cutoff; it overlaps W36 without replacing Vintage A.
  eid_b=BusinessWorkflowAcceptanceService().accept(cid,uid,did,request_metadata={'params':{**context('2026-W35'),'horizon':4}});await BusinessWorkflowScheduler(s).run_next_ready(eid_b,cid)
  s.close();s=SessionLocal();store=RuntimeStore(s); va=s.query(ForecastVintage).filter_by(execution_id=eid_a).one();vb=s.query(ForecastVintage).filter_by(execution_id=eid_b).one();pa=s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=va.id).order_by(ForecastVintagePoint.horizon_index).all();pb=s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=vb.id).order_by(ForecastVintagePoint.horizon_index).all()
  assert [x.target_period for x in pa]==['2026-W33','2026-W34','2026-W35','2026-W36'] and [x.target_period for x in pb]==['2026-W36','2026-W37','2026-W38','2026-W39'] and va.runtime_result_reference_id!=vb.runtime_result_reference_id
  assert va.forecast_available_at and va.input_cutoff_period=='2026-W32' and va.forecast_origin_period=='2026-W32' and all(x.product_level=='finished_good' and x.product_group=='G' and x.product_class=='C' for x in pa+pb)
  assert len([x for x in pa+pb if x.target_period=='2026-W36'])==2 and canonical_targets('2026-W52',2)==['2026-W53','2027-W01']
  va_id,va_ref_id,vb_id=va.id,va.runtime_result_reference_id,vb.id;ref=s.query(RuntimeResultReference).filter_by(id=va_ref_id).one(); before=s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=va_id).count(); assert ForecastVintageService(s).project(store.get_execution(eid_a,cid),ref,{**context('2026-W32'),'horizon':4}).id==va_id;s.commit();assert s.query(ForecastVintage).filter_by(runtime_result_reference_id=ref.id).count()==1 and s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=va_id).count()==before
  s.close();s=SessionLocal();assert s.query(ForecastVintage).filter_by(execution_id=eid_a).one().runtime_result_reference_id==va_ref_id and s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=vb_id).count()==4
  print('PHASE3AA3 PASS',json.dumps({'standalone_points':4,'business_points':4,'overlap':'2026-W36','year_boundary':canonical_targets('2026-W52',2),'idempotent':True}),flush=True)
 finally:
  if s: s.rollback()
  if c:
   ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid).all()];vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=cid).all()];s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter_by(company_id=cid).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(ActualWeeklyRevision).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=cid).delete(synchronize_session=False);s.query(Dataset).filter_by(company_id=cid).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False);s.query(User).filter_by(id=uid).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':asyncio.run(main())
