import asyncio,hashlib,json,sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.engine.local_forecast_runner import LocalForecastRunner
from app.engine.capability_dataflow import assemble_simulation_business_input
async def main():
 s=SessionLocal(); p='phase2f_'+str(uuid7()).replace('-',''); c=u=d=None
 try:
  c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush()
  data={'items':[{'sku_code':'A','demand_history':[10,12,11,13,12,14,13,15,14,16,15,17],'lead_time_days':14,'initial_stock':80,'eoq':50,'rop':45},{'sku_code':'B','demand_history':[0,8,0,12,0,5,0,14,0,7,0,11],'lead_time_days':21,'initial_stock':50,'eoq':30,'safety_stock':12}]}
  d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256(json.dumps(data).encode()).hexdigest(),source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,data),is_active=True);s.add(d);s.commit()
  start=perf_counter();x=await WorkflowDispatcher().dispatch_single_analysis(c.id,u.id,d.id,'simulation',params={'n_simulations':30,'weeks':6});accept=(perf_counter()-start)*1000; eid=x['execution_id']; tasks=s.query(RuntimeTask).filter_by(execution_id=eid).all();assert len(tasks)==1 and tasks[0].capability=='simulation' and tasks[0].dependencies==[]
  t=perf_counter();await LocalForecastRunner().run(eid);dur=(perf_counter()-t)*1000; fresh=WorkflowDispatcher();status=await fresh.get_execution_status(eid);result=await fresh.get_execution_result(eid);s.expire_all();e=s.query(RuntimeExecution).filter_by(execution_id=eid).one();a=s.query(RuntimeTaskAttempt).filter_by(execution_id=eid).one();refs=s.query(RuntimeResultReference).filter_by(execution_id=eid).all();assert status['state']=='completed' and status['progress']==100 and e.state=='completed' and a.state=='completed' and len(refs)==1 and result['result']==refs[0].inline_result and len(result['result']['items'])==2
  biz=assemble_simulation_business_input({'policies':{'A':{'initial_stock':1,'eoq':1}}},{'forecast':{'result':{'items':[{'material_code':'A','forecast':[1,2,3]}]},'provenance':{}},'safety_stock':{'result':{'items':[{'material_code':'A','safety_stock':2,'effective_lead_time_used':14}]},'provenance':{}}});assert biz['forecast_source']=='upstream'
  print('PHASE2F PASS',json.dumps({'acceptance_ms':round(accept,3),'simulation_ms':round(dur,3),'skus':2,'n_simulations':30,'weeks':6,'attempts':1}),flush=True)
 finally:
  s.rollback()
  if c:
   ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=c.id).all()];s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter_by(source_type=p).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=u.id).delete(synchronize_session=False);s.query(User).filter_by(email=p+'@x.invalid').delete(synchronize_session=False);s.query(Company).filter_by(tax_id=p).delete(synchronize_session=False);s.commit()
  s.close()
if __name__=='__main__':asyncio.run(main())
