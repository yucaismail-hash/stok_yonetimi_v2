"""Test-only canonical Actual Ledger fixtures for Pattern Intelligence."""
from dataclasses import dataclass
from uuid_extensions import uuid7
import hashlib
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.security import CompanyEncryptionKey
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.services.security import EncryptionService

SHAPES={
 'stable':[100,101,99,100,101,100,99,100,101,100,99,100],
 'trend':[50,55,60,65,70,75,80,85,90,95,100,105],
 'volatile':[20,180,25,175,20,180,25,175,20,180,25,175],
 'intermittent':[0,0,50,0,0,50,0,0,50,0,0,50],
 'lumpy':[0,0,20,0,0,180,0,0,35,0,0,220],
 'missing':[100,101,99,100,101,100,99,100],
 'insufficient':[100,101,99,100],
}
@dataclass(frozen=True)
class PatternFixture:
 company_id:object;user_id:object;dataset_id:object;material_code:str;demand_type:str;product_level:str;periods:tuple[str,...]
def create(shape,material_code=None,demand_type='sales',product_level='finished_good',context=None):
 s=SessionLocal()
 try:
  if context is None:
   tag='pattern_fixture_'+str(uuid7());c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();d=Dataset(id=uuid7(),company_id=c.id,user_id=u.id,uploaded_by=u.id,dataset_hash=hashlib.sha256(tag.encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(u.id,{'items':[]}),is_active=True);s.add(d);s.commit();context={'company_id':c.id,'user_id':u.id,'dataset_id':d.id}
  values=SHAPES[shape];code=material_code or shape.upper();weeks=[w for w in range(1,len(values)+1) if not(shape=='missing' and w in {5,9})]; values=values if shape!='missing' else values[:len(weeks)]
  rows=[{'material_code':code,'period':f'2026-W{w:02d}','quantity':v,'product_level':product_level,'product_group':'G','product_class':'C'} for w,v in zip(weeks,values)]
  ActualWeeklyLedgerService().ingest_dataset_actuals(context['company_id'],context['user_id'],context['dataset_id'],rows,demand_type)
  return PatternFixture(context['company_id'],context['user_id'],context['dataset_id'],code,demand_type,product_level,tuple(r['period'] for r in rows))
 finally:s.close()
def cleanup(fixture):
 s=SessionLocal()
 try:
  s.query(ActualWeeklyRevision).filter_by(company_id=fixture.company_id).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=fixture.company_id).delete(synchronize_session=False);s.query(Dataset).filter_by(id=fixture.dataset_id).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=fixture.user_id).delete(synchronize_session=False);s.query(User).filter_by(id=fixture.user_id).delete(synchronize_session=False);s.query(Company).filter_by(id=fixture.company_id).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=fixture.company_id).count()==0
 finally:s.close()
