import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from sqlalchemy.orm import configure_mappers
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference,RuntimeCheckpoint
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
def main():
 s=SessionLocal();p='phase3a1_'+str(uuid7()).replace('-','');c=u=d=None
 try:
  configure_mappers();c=Company(id=uuid7(),name=p,tax_id=p);u=User(id=uuid7(),company_id=c.id,email=p+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=p,source_type=p,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,{'items':[]}),is_active=True);s.add(d);s.commit();eid=BusinessWorkflowAcceptanceService().accept(c.id,u.id,d.id,request_metadata={'probe':True});s.expire_all();e=s.query(RuntimeExecution).filter_by(execution_id=eid).one();ts=s.query(RuntimeTask).filter_by(execution_id=eid).order_by(RuntimeTask.task_order).all();assert e.state=='queued' and float(e.progress)==0 and len(ts)==4 and [t.dependencies for t in ts]==[[],['forecast'],['forecast','safety_stock'],['safety_stock']] and s.query(RuntimeTaskAttempt).filter_by(execution_id=eid).count()==0 and s.query(RuntimeResultReference).filter_by(execution_id=eid).count()==0 and s.query(RuntimeCheckpoint).filter_by(execution_id=eid).count()==0;print('PHASE3A1 PASS',eid,flush=True)
 finally:
  s.rollback()
  if c:
   ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=c.id).all()];s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter_by(source_type=p).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=u.id).delete(synchronize_session=False);s.query(User).filter_by(email=p+'@x.invalid').delete(synchronize_session=False);s.query(Company).filter_by(tax_id=p).delete(synchronize_session=False);s.commit();s.close()
if __name__=='__main__':main()
