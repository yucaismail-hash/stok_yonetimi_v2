"""Focused PostgreSQL proof for generic RuntimeResult cutoff authority."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
def ctx(tag):
 s=SessionLocal()
 try:
  c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=tag,source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,{'items':[]}),is_active=True);s.add(d);s.commit();return c.id,u.id,d.id
 finally:s.close()
def add(c,u,d,kind,material,metadata):
 s=SessionLocal()
 try:
  e=RuntimeExecution(execution_id=uuid7(),company_id=c,user_id=u,dataset_id=d,workflow_id='cutoff-probe',analysis_type=kind,state='completed',metadata_=metadata);s.add(e);s.flush();r=RuntimeResultReference(id=uuid7(),company_id=c,execution_id=e.execution_id,result_type=kind,result_version='1',contract_version='1',storage_kind='inline_jsonb',inline_result={'items':[{'material_code':material}]},validation_status='validated');s.add(r);s.commit();return r.id
 finally:s.close()
def clean(c,u,d):
 s=SessionLocal()
 try:
  ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=c).all()];s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(Dataset).filter_by(id=d).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=u).delete(synchronize_session=False);s.query(User).filter_by(id=u).delete(synchronize_session=False);s.query(Company).filter_by(id=c).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=c).count()==0
 finally:s.close()
def state(c,kind,material='A',cutoff='2026-W10'):
 s=SessionLocal()
 try:return DecisionEvidenceResolver()._runtime(s,c,kind,material,cutoff)
 finally:s.close()
def main():
 roots=[]
 try:
  a=ctx('decision_cutoff_a_'+str(uuid7()));roots.append(a);b=ctx('decision_cutoff_b_'+str(uuid7()));roots.append(b);c,u,d=a;t1={'params':{'analysis_cutoff_period':'2026-W10','forecast_cutoff_period':'2026-W11','forecast_vintage':{'input_cutoff_period':'2026-W12'}}};t2={'params':{'analysis_cutoff_period':'2026-W12'}}
  for kind in ('safety_stock','supplier','simulation','backtest'):add(c,u,d,kind,'A',t1)
  before={kind:state(c,kind) for kind in ('safety_stock','supplier','simulation','backtest')};assert all(x['status']=='AVAILABLE' and x['cutoff_period']=='2026-W10' for x in before.values())
  fresh={kind:state(c,kind) for kind in before};assert fresh==before
  for kind in before:add(c,u,d,kind,'A',t2)
  after={kind:state(c,kind) for kind in before};assert {k:v['source_id'] for k,v in before.items()}=={k:v['source_id'] for k,v in after.items()}
  add(c,u,d,'safety_stock','B',t2);add(c,u,d,'simulation','C',{});add(b[0],b[1],b[2],'safety_stock','A',t2)
  assert state(c,'safety_stock','B')['status']=='INCOMPATIBLE' and state(c,'simulation','A','2026-W09')['reason']=='FUTURE_EVIDENCE';assert state(c,'backtest','MISSING')['status']=='ABSENT'
  unknown=state(c,'simulation','C','2026-W10');assert unknown['status']=='INCOMPATIBLE' and unknown['reason']=='CUTOFF_UNKNOWN'
  print('PHASE 3D2 CUTOFF PROBE PASS',{'t1':{k:v['cutoff_period'] for k,v in before.items()},'future_non_interference':True},flush=True)
 finally:
  for root in reversed(roots):clean(*root)
if __name__=='__main__':main()
