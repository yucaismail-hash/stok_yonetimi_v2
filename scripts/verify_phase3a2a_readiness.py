import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from sqlalchemy.orm import configure_mappers
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler,BusinessWorkflowReadinessError
from app.engine.runtime_store import RuntimeStore
def states(rows):return {x['task_id']:x for x in rows}
def main():
 s=SessionLocal();p='phase3a2a_'+str(uuid7()).replace('-','');c=u=d=None
 try:
  configure_mappers();c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();cid=c.id;uid=u.id;d=Dataset(id=uuid7(),company_id=cid,user_id=uid,uploaded_by=uid,dataset_hash=p,source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(uid,{}),is_active=True);s.add(d);s.commit();eid=BusinessWorkflowAcceptanceService().accept(cid,uid,d.id);store=RuntimeStore(s);r=states(BusinessWorkflowScheduler(s).readiness(eid,cid));assert r['forecast']['ready'] and not r['safety_stock']['ready'] and not r['simulation']['ready'] and not r['backtest']['ready']
  ts={t.task_id:t for t in store.get_tasks(eid,cid)};ts['forecast'].state='completed';store.register_result_reference(cid,eid,'forecast',{'items':[]},runtime_task_id=ts['forecast'].id);s.commit();r=states(BusinessWorkflowScheduler(s).readiness(eid,cid));assert r['safety_stock']['ready'] and not r['simulation']['ready'] and not r['backtest']['ready']
  ts['safety_stock'].state='completed';store.register_result_reference(cid,eid,'safety_stock',{'items':[]},runtime_task_id=ts['safety_stock'].id);s.commit();s.close();s=SessionLocal();r=BusinessWorkflowScheduler(s).readiness(eid,cid);ready=[x['task_id'] for x in r if x['ready']];assert ready==['simulation','backtest'];assert s.query(RuntimeTaskAttempt).filter_by(execution_id=eid).count()==0
  s.query(RuntimeResultReference).filter_by(execution_id=eid,result_type='safety_stock').update({'validation_status':'invalid'});s.commit();assert not states(BusinessWorkflowScheduler(s).readiness(eid,cid))['backtest']['ready']
  bad=RuntimeTask(execution_id=eid,company_id=cid,workflow_id='x',task_id='bad',capability='x',task_order=9,required=True,skippable=False,dependencies=['missing'],state='pending',max_attempts=1);s.add(bad);s.commit()
  try: BusinessWorkflowScheduler(s).readiness(eid,cid);raise AssertionError()
  except BusinessWorkflowReadinessError: pass
  s.delete(bad);s.commit();e=store.get_execution(eid,cid);e.state='completed';s.commit();assert not any(x['ready'] for x in BusinessWorkflowScheduler(s).readiness(eid,cid));print('PHASE3A2A PASS',flush=True)
 finally:
  try:s.rollback()
  except:pass
  if c:
   ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid).all()];s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter_by(source_type=p).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False);s.query(User).filter_by(email=p+'@x.invalid').delete(synchronize_session=False);s.query(Company).filter_by(tax_id=p).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':main()
