"""PostgreSQL proof for Event Intelligence's durable current projection."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sys, threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.event_association import EventAssociationService
from app.application.event_intelligence_materialization import EventIntelligenceMaterializationService
from app.application.event_observations import EventObservationService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.event_observation import EventObservation,EventRevision
from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
from app.models.learning_evidence import LearningEvidence
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.runtime import RuntimeExecution,RuntimeResultReference
from app.models.company import Company,User,UserMaterial
from app.models.dataset import Dataset
from app.models.security import CompanyEncryptionKey
from scripts.verify_phase3c7b2_event_association import make_context,ingest,event,vintage,counts

def clean(root):
 s=SessionLocal()
 try:
  ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=root['company_id']).all()];vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=root['company_id']).all()]
  s.query(EventIntelligenceMemory).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(EventRevision).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(EventObservation).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(ActualWeeklyRevision).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(UserMaterial).filter_by(company_id=root['company_id']).delete(synchronize_session=False);s.query(Dataset).filter_by(id=root['dataset_id']).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=root['user_id']).delete(synchronize_session=False);s.query(User).filter_by(id=root['user_id']).delete(synchronize_session=False);s.query(Company).filter_by(id=root['company_id']).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=root['company_id']).count()==0
 finally:s.close()

def fixture(root):
 values={w:100 for w in range(1,32)};values.update({5:130,10:130,6:70,11:70,7:101,12:99,8:130,13:70,15:130,16:130,17:130,18:130,20:130,21:130,22:130,28:130,30:130})
 ingest(root,'sales',values);ingest(root,'consumption',{w:40 for w in range(1,32)})
 ids={}
 for ident,weeks in {'POS':(5,10),'NEG':(6,11),'CLEAR':(7,12),'MIX':(8,13),'ONE':(20,),'SCOPE_G':(15,16),'SCOPE_C':(17,18)}.items():ids[ident]=[event(root,ident,f'{ident}-{w}',w,scope='PRODUCT_GROUP' if ident=='SCOPE_G' else 'PRODUCT_CLASS' if ident=='SCOPE_C' else 'MATERIAL',value='G' if ident=='SCOPE_G' else 'C' if ident=='SCOPE_C' else 'SKU').event_id for w in weeks]
 ids['COMPANY']=[event(root,'SCOPE_CO',f'SCOPE_CO-{w}',w,scope='COMPANY',value=None).event_id for w in (21,22)];ids['CONSUMPTION']=[event(root,'POS','POS-C-5',5,demand='consumption').event_id];vintage(root,target_weeks=(5,10,15,16,17,18,19,21,22,24));return ids

def main():
 roots=[]
 try:
  root=make_context();roots.append(root);other=make_context();roots.append(other);ids=fixture(root);fixture(other);cutoff='2026-W25';m=EventIntelligenceMaterializationService();a=EventAssociationService()
  first=m.materialize(root['company_id'],'SKU','sales','POS',cutoff);same=m.materialize(root['company_id'],'SKU','sales','POS',cutoff);assert(first.status,same.status,first.row_version,same.row_version)==('CREATED','UNCHANGED',1,1)
  assert m.materialize(root['company_id'],'SKU','sales','NEG',cutoff).status=='CREATED';assert m.materialize(root['company_id'],'SKU','sales','CLEAR',cutoff).status=='CREATED';assert m.materialize(root['company_id'],'SKU','sales','MIX',cutoff).status=='CREATED'
  # Scope sources stay material-level memories with durable source scope lineage.
  for ident in ('SCOPE_G','SCOPE_C','SCOPE_CO'):assert m.materialize(root['company_id'],'SKU','sales',ident,cutoff).status=='CREATED'
  assert m.get_current(root['company_id'],'SKU','sales','SCOPE_G').source_scope_metadata['event_scopes'][0][1]=='PRODUCT_GROUP'
  assert m.materialize(root['company_id'],'SKU','sales','ONE',cutoff).status=='NOT_MATERIALIZED'
  consumption=m.materialize(root['company_id'],'SKU','consumption','POS',cutoff);assert consumption.status=='NOT_MATERIALIZED' # one consumption occurrence is intentionally insufficient
  # Add recurring consumption evidence to prove demand isolation.
  event(root,'POS','POS-C-10',10,demand='consumption');consumption=m.materialize(root['company_id'],'SKU','consumption','POS',cutoff);assert consumption.status=='CREATED' and m.get_current(root['company_id'],'SKU','sales','POS').id==first.memory_id and consumption.memory_id!=first.memory_id
  event(root,'POS','POS-15',15);recurring=m.materialize(root['company_id'],'SKU','sales','POS',cutoff);assert recurring.status=='UPDATED' and recurring.memory_id==first.memory_id and recurring.row_version==2
  # Actual accepted updates, rejected corrections do not; event accepted/rejected follow the same source contract.
  ledger=ActualWeeklyLedgerService();p=ingest(root,'sales',{5:150});ledger.approve_revision(root['company_id'],p['revision_ids'][0],root['user_id']);actual_updated=m.materialize(root['company_id'],'SKU','sales','POS',cutoff);assert actual_updated.status=='UPDATED'
  p=ingest(root,'sales',{10:999});ledger.reject_revision(root['company_id'],p['revision_ids'][0],root['user_id']);assert m.materialize(root['company_id'],'SKU','sales','POS',cutoff).status=='UNCHANGED'
  ev=EventObservationService();r=ev.propose_correction(root['company_id'],ids['POS'][0],root['user_id'],event_type='campaign_v2');ev.accept_correction(root['company_id'],r.revision_id,root['user_id']);assert m.materialize(root['company_id'],'SKU','sales','POS',cutoff).status=='UPDATED'
  r=ev.propose_correction(root['company_id'],ids['POS'][1],root['user_id'],event_type='ignored');ev.reject_correction(root['company_id'],r.revision_id,root['user_id']);assert m.materialize(root['company_id'],'SKU','sales','POS',cutoff).status=='UNCHANGED'
  # Same cutoff ignores later canonical state; later cutoff refreshes only when evidence changes.
  old=m.get_current(root['company_id'],'SKU','sales','POS');ingest(root,'sales',{26:999});event(root,'POS','POS-26',26);vintage(root,available_at=datetime.now(timezone.utc));assert m.materialize(root['company_id'],'SKU','sales','POS',cutoff).status=='UNCHANGED';later=m.materialize(root['company_id'],'SKU','sales','POS','2026-W26');assert later.status=='UPDATED'
  stale=a.calculate(root['company_id'],'SKU','sales','POS',cutoff);s=SessionLocal()
  try:assert m.persist_result(s,stale).status=='STALE_RESULT'
  finally:s.close()
  # First-write race is PostgreSQL-backed through independent service/session instances.
  event(root,'RACE','RACE-28',28);event(root,'RACE','RACE-30',30);barrier=threading.Barrier(2)
  def race():barrier.wait();return EventIntelligenceMaterializationService().materialize(root['company_id'],'SKU','sales','RACE','2026-W31')
  with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(lambda _:race(),range(2)))
  assert sorted(x.status for x in out)==['CREATED','UNCHANGED'],[(x.status,x.row_version,x.source_fingerprint) for x in out]
  # Cancellation and overlap leave no fabricated new projection.
  ev.cancel(root['company_id'],ids['ONE'][0],root['user_id']);assert m.materialize(root['company_id'],'SKU','sales','ONE',cutoff).status=='NOT_MATERIALIZED'
  event(root,'OVER','OVER-5',5);event(root,'OVER','OVER-10',10);event(root,'OTHER','OTHER-5',5);assert m.materialize(root['company_id'],'SKU','sales','OVER',cutoff).status=='NOT_MATERIALIZED'
  assert m.get_current(other['company_id'],'SKU','sales','POS') is None
  before_fresh=m.get_current(root['company_id'],'SKU','sales','POS');fresh=EventIntelligenceMaterializationService().get_current(root['company_id'],'SKU','sales','POS');assert fresh and (fresh.classification,fresh.confidence,fresh.occurrence_count,fresh.baseline_method,fresh.cutoff_period,fresh.row_version,fresh.source_fingerprint)==(before_fresh.classification,before_fresh.confidence,before_fresh.occurrence_count,before_fresh.baseline_method,before_fresh.cutoff_period,before_fresh.row_version,before_fresh.source_fingerprint)
  before=counts(root['company_id']);assert before[0:2] and s.query(EventIntelligenceMemory).filter_by(company_id=root['company_id']).count()>=7
  print('PHASE 3C7B3 PROBE PASS',{'first':first.status,'repeat':same.status,'recurring':recurring.status,'stale':'STALE_RESULT','race':[x.status for x in out],'rows':s.query(EventIntelligenceMemory).filter_by(company_id=root['company_id']).count()},flush=True)
 finally:
  for root in reversed(roots):clean(root)
if __name__=='__main__':main()
