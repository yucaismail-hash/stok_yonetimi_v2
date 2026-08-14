import asyncio,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
from app.services.security import EncryptionService
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
async def main():
 s=SessionLocal();p='d2_business_cutoff_'+str(uuid7()).replace('-','');c=u=d=None
 try:
  level=sys.argv[1] if len(sys.argv)>1 else 'finished_good';demand=sys.argv[2] if len(sys.argv)>2 else 'sales'
  c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();data={'items':[{'sku_code':'A','demand_history':list(range(10,30)),'lead_time_days':14,'initial_stock':80,'eoq':50,'rop':45,'product_level':level,'product_group':None,'product_class':None}]};d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256((p+json.dumps(data)).encode()).hexdigest(),source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,data),is_active=True);s.add(d);s.commit()
  rows=[{'material_code':'A','period':f'2026-W{i:02d}','quantity':10+i,'product_level':level,'product_group':None,'product_class':None} for i in range(1,21)];ActualWeeklyLedgerService().ingest_dataset_actuals(c.id,u.id,d.id,rows,demand)
  eid=BusinessWorkflowAcceptanceService().accept(c.id,u.id,d.id,request_metadata={'params':{'forecast_vintage':{'demand_type':demand}}});
  for _ in range(5):
   s.close();s=SessionLocal();out=await BusinessWorkflowScheduler(s).run_next_ready(eid,c.id)
   if out is None:break
  s.expire_all();e=s.query(RuntimeExecution).filter_by(execution_id=eid).one();refs=s.query(RuntimeResultReference).filter_by(execution_id=eid).all();assert e.state=='completed' and float(e.progress)==100,{'state':e.state,'progress':float(e.progress),'tasks':[(t.task_id,t.state,t.error_summary) for t in s.query(RuntimeTask).filter_by(execution_id=eid).all()]}
  cutoff=e.metadata_['request_metadata']['params']['forecast_cutoff_period'];r=DecisionEvidenceResolver();proof={kind:r._runtime(s,c.id,kind,'A',cutoff) for kind in ('safety_stock','simulation','backtest')};assert all(x['status']=='AVAILABLE' and x['cutoff_period']==cutoff for x in proof.values());v=s.query(ForecastVintage).filter_by(execution_id=eid).one();point=s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=v.id).first();s.close();s=SessionLocal();fresh=s.query(ForecastVintage).filter_by(id=v.id).one();assert (fresh.demand_type,point.product_level,fresh.input_cutoff_period)==(demand,level,cutoff);print('PHASE 3D2 BUSINESS CUTOFF PASS',{'execution_id':str(eid),'cutoff':cutoff,'level':level,'demand_type':demand,'modules':proof},flush=True)
 finally:
  if s:
   s.rollback()
   if c:
    ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=c.id).all()];vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=c.id).all()];s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(ActualWeeklyRevision).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=c.id).delete(synchronize_session=False);s.query(Dataset).filter_by(id=d.id).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=u.id).delete(synchronize_session=False);s.query(User).filter_by(id=u.id).delete(synchronize_session=False);s.query(Company).filter_by(id=c.id).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':asyncio.run(main())
