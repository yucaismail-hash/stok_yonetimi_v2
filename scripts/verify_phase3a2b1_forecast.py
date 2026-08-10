import asyncio,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
async def main():
 s=SessionLocal();p='phase3a2b1_'+str(uuid7()).replace('-','');c=u=d=None
 try:
  c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();cid=c.id;uid=u.id;data={'items':[{'sku_code':'A','demand_history':[1,2,3,4,5,6,7,8,9,10,11,12],'lead_time_days':14,'initial_stock':10,'eoq':5}]};d=Dataset(id=uuid7(),company_id=cid,user_id=uid,uploaded_by=uid,dataset_hash=p,source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(uid,data),is_active=True);s.add(d);s.commit();eid=BusinessWorkflowAcceptanceService().accept(cid,uid,d.id)
  for _ in range(4): await BusinessWorkflowScheduler(s).run_next_ready(eid,cid);s.close();s=SessionLocal()
  e=s.query(RuntimeExecution).filter_by(execution_id=eid).one();ts=s.query(RuntimeTask).filter_by(execution_id=eid).all();refs=s.query(RuntimeResultReference).filter_by(execution_id=eid).all();assert e.state=='completed' and float(e.progress)==100 and len(ts)==4 and all(x.state=='completed' for x in ts) and s.query(RuntimeTaskAttempt).filter_by(execution_id=eid).count()==4 and len(refs)==4 and not any(x['ready'] for x in BusinessWorkflowScheduler(s).readiness(eid,cid));print('PHASE3A2B2B2 PASS',flush=True)
 finally:
  s.rollback()
  if c:
   ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid).all()];s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter_by(source_type=p).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False);s.query(User).filter_by(email=p+'@x.invalid').delete(synchronize_session=False);s.query(Company).filter_by(tax_id=p).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':asyncio.run(main())
