"""Focused PostgreSQL proof for canonical Event Observation facts and revisions."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys, threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.application.event_observations import EventObservationError,EventObservationService
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.dataset import DatasetEvent
from app.models.event_observation import EventObservation,EventRevision
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.supplier_learning_memory import SupplierLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution

def fixture(label):
 s=SessionLocal();tag='event_observation_'+label+'_'+str(uuid7())
 try:
  c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.commit();return {'company_id':c.id,'user_id':u.id}
 finally:s.close()
def clean(root):
 s=SessionLocal()
 try:
  s.query(EventRevision).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(EventObservation).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(User).filter_by(id=root['user_id']).delete(synchronize_session=False);s.query(Company).filter_by(id=root['company_id']).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=root['company_id']).count()==0
 finally:s.close()
def counts(cid):
 s=SessionLocal()
 try:return tuple(s.query(x).filter_by(company_id=cid).count() for x in (LearningEvidence,LearningRefreshDelivery,PatternLearningMemory,CompanyLearningMemoryV2,SupplierLearningMemory,RetrainingJob,RuntimeExecution))
 finally:s.close()
def create(svc,root,ref,**changes):
 values=dict(event_identity='SPRING_CAMPAIGN',event_type='campaign',source_occurrence_reference=ref,scope_type='MATERIAL',scope_value='MAT-X',demand_type='sales',start_date=date(2026,3,2),end_date=date(2026,3,8),authority_type='COMPANY_EXPLICIT',source_system='company_event',provenance={'fixture':ref});values.update(changes);return svc.create(root['company_id'],**values)
def main():
 roots=[]
 try:
  a=fixture('a');roots.append(a);b=fixture('b');roots.append(b);svc=EventObservationService();zero=counts(a['company_id'])
  # A/B/C/D: occurrence identity is deterministic but recurring family dates are independent.
  first=create(svc,a,'SPRING-2026');same=create(svc,a,'SPRING-2026');assert(first.status,same.status)==('CREATED','ALREADY_EXISTS')
  barrier=threading.Barrier(2)
  def race():barrier.wait();return create(EventObservationService(),a,'SPRING-CONCURRENT')
  with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(lambda _:race(),range(2)))
  assert sorted(x.status for x in out)==['ALREADY_EXISTS','CREATED']
  recurring=create(svc,a,'SPRING-2027',start_date=date(2027,3,1),end_date=date(2027,3,7));assert recurring.status=='CREATED' and recurring.event_id!=first.event_id
  # E/F/G/H: explicit scope and demand type identities remain independent.
  group=create(svc,a,'GROUP',scope_type='PRODUCT_GROUP',scope_value='G1');klass=create(svc,a,'CLASS',scope_type='PRODUCT_CLASS',scope_value='C1');company=create(svc,a,'COMPANY',scope_type='COMPANY',scope_value=None);consumption=create(svc,a,'CONSUMPTION',demand_type='consumption')
  assert len(svc.query_current(a['company_id'],scope_type='MATERIAL',scope_value='MAT-X',demand_type='sales'))==3
  assert svc.get(a['company_id'],consumption.event_id).demand_type=='consumption'
  # I/J/K/L/N: accepted changes retain snapshots; rejected never changes current; cancellation is a state revision.
  before=svc.get(a['company_id'],first.event_id);base_at=before.current_accepted_at
  date_rev=svc.propose_correction(a['company_id'],first.event_id,a['user_id'],end_date=date(2026,3,10));assert svc.accept_correction(a['company_id'],date_rev.revision_id,a['user_id']).status=='ACCEPTED'
  after_date=svc.get(a['company_id'],first.event_id);assert after_date.end_date==date(2026,3,10) and after_date.current_evidence_fingerprint!=before.current_evidence_fingerprint
  scope_rev=svc.propose_correction(a['company_id'],first.event_id,a['user_id'],scope_type='PRODUCT_GROUP',scope_value='G2');assert svc.accept_correction(a['company_id'],scope_rev.revision_id,a['user_id']).status=='ACCEPTED';assert svc.get(a['company_id'],first.event_id).scope_value=='G2'
  rejected=svc.propose_correction(a['company_id'],first.event_id,a['user_id'],event_type='promotion');fp=svc.get(a['company_id'],first.event_id).current_evidence_fingerprint;assert svc.reject_correction(a['company_id'],rejected.revision_id,a['user_id']).status=='REJECTED' and svc.get(a['company_id'],first.event_id).current_evidence_fingerprint==fp
  cancelled=svc.cancel(a['company_id'],first.event_id,a['user_id']);assert cancelled.status=='ACCEPTED' and svc.get(a['company_id'],first.event_id).status=='CANCELLED'
  assert svc.as_of(a['company_id'],first.event_id,base_at)['end_date']=='2026-03-08'
  assert svc.as_of(a['company_id'],first.event_id,datetime.now(timezone.utc))['status']=='CANCELLED'
  # M/O/P/Q/R: tenant and invalid authority/scope are rejected; dataset rows are not imported; writes are isolated.
  assert svc.get(b['company_id'],first.event_id) is None
  for action in (lambda:svc.propose_correction(b['company_id'],first.event_id,b['user_id'],status='CANCELLED'),lambda:create(svc,a,'INVALID',scope_type='UNKNOWN'),lambda:create(svc,a,'INVALID2',scope_type='MATERIAL',scope_value=None),lambda:create(svc,a,'INVALID3',authority_type='PUBLIC_REFERENCE',public_reference_id=None),lambda:create(svc,a,'INVALID4',start_date=date(2026,3,9),end_date=date(2026,3,1))):
   try:action();raise AssertionError('invalid event accepted')
   except (EventObservationError,LookupError):pass
  s=SessionLocal()
  try:assert s.query(DatasetEvent).count()==0
  finally:s.close()
  fresh=EventObservationService().get(a['company_id'],first.event_id);assert(fresh.status,fresh.scope_type,fresh.scope_value)==('CANCELLED','PRODUCT_GROUP','G2')
  assert counts(a['company_id'])==zero
  print('PHASE 3C7B1 PROBE PASS',{'created':first.status,'concurrent':[x.status for x in out],'revisions':len(svc.query_current(a['company_id'],event_identity='SPRING_CAMPAIGN')),'cancelled':cancelled.status},flush=True)
 finally:
  for root in reversed(roots):clean(root)
if __name__=='__main__':main()
