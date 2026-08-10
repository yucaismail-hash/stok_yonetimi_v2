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
async def main():
 s=SessionLocal();p='phase2h_'+str(uuid7()).replace('-','');c=u=d=None
 try:
  c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();data={'suppliers':{'S1':{'name':'Good','delivery_records':[{'planned_days_ago':12,'actual_days_ago':11,'planned_qty':100,'actual_qty':100}]},'S2':{'name':'Risky','delivery_records':[{'planned_days_ago':20,'actual_days_ago':5,'planned_qty':100,'actual_qty':60,'defects':5}]}},'supplier_mapping':{'MAT_A':{'supplier_id':'S1','share':.7},'MAT_B':{'supplier_id':'S2','share':.3}}};d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256(json.dumps(data).encode()).hexdigest(),source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,data),is_active=True);s.add(d);s.commit();t=perf_counter();x=await WorkflowDispatcher().dispatch_single_analysis(c.id,u.id,d.id,'supplier');accept=(perf_counter()-t)*1000;eid=x['execution_id'];assert len(s.query(RuntimeTask).filter_by(execution_id=eid).all())==1;t=perf_counter();await LocalForecastRunner().run(eid);dur=(perf_counter()-t)*1000;fresh=WorkflowDispatcher();status=await fresh.get_execution_status(eid);result=await fresh.get_execution_result(eid);s.expire_all();e=s.query(RuntimeExecution).filter_by(execution_id=eid).one();a=s.query(RuntimeTaskAttempt).filter_by(execution_id=eid).one();refs=s.query(RuntimeResultReference).filter_by(execution_id=eid).all();assert e.state=='completed' and float(e.progress)==100 and a.state=='completed' and len(refs)==1 and status['state']=='completed' and status['progress']==100 and result['result']==refs[0].inline_result and len(result['result']['suppliers'])==2
  for bad in ({'supplier_mapping':{}},{'suppliers':{}},{'suppliers':{'S1':{}},'supplier_mapping':{'M':{'supplier_id':'NO'}}}):
   q=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=str(uuid7()),source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,bad),is_active=True);s.add(q);s.commit();z=await WorkflowDispatcher().dispatch_single_analysis(c.id,u.id,q.id,'supplier');await LocalForecastRunner().run(z['execution_id']);s.expire_all();fe=s.query(RuntimeExecution).filter_by(execution_id=z['execution_id']).one();assert fe.state=='failed' and s.query(RuntimeResultReference).filter_by(execution_id=z['execution_id']).count()==0
  print('PHASE2H PASS',json.dumps({'acceptance_ms':round(accept,3),'supplier_ms':round(dur,3),'suppliers':2,'mappings':2,'attempts':1}),flush=True)
 finally:
  s.rollback()
  if c:
   ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=c.id).all()];s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter(Dataset.source_type==p).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=u.id).delete(synchronize_session=False);s.query(User).filter_by(email=p+'@x.invalid').delete(synchronize_session=False);s.query(Company).filter_by(tax_id=p).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':asyncio.run(main())
