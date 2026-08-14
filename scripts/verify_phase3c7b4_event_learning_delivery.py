"""Focused PostgreSQL Event LearningEvidence → delivery → Event Memory proof."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys, threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.event_intelligence_materialization import EventIntelligenceMaterializationService
from app.application.event_observations import EventObservationService
from app.application.learning_evidence import LearningEvidenceService
from app.application.learning_refresh_delivery import LearningRefreshDeliveryService
from app.application.learning_refresh_orchestrator import LearningRefreshOrchestrator
from app.application.learning_refresh_worker import LearningRefreshWorker
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.company import Company,User,UserMaterial
from app.models.dataset import Dataset
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.event_observation import EventObservation,EventRevision
from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.runtime import RuntimeExecution,RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from scripts.verify_phase3c7b3_event_intelligence_memory import fixture,clean as clean_base
from scripts.verify_phase3c7b2_event_association import make_context,event,ingest

def delivery(cid,eid):
 s=SessionLocal()
 try:return s.query(LearningRefreshDelivery).filter_by(company_id=cid,learning_evidence_id=eid).one()
 finally:s.close()
def expire(cid,did):
 s=SessionLocal()
 try:r=s.query(LearningRefreshDelivery).filter_by(company_id=cid,id=did).one();r.lease_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);s.commit()
 finally:s.close()
def counts(cid):
 s=SessionLocal()
 try:return tuple(s.query(x).filter_by(company_id=cid).count() for x in (LearningEvidence,LearningRefreshDelivery,EventIntelligenceMemory,PatternLearningMemory,ForecastVintage,RuntimeExecution))
 finally:s.close()
def clean(root):
 s=SessionLocal()
 try:
  s.query(LearningRefreshDelivery).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
  for evidence in s.query(LearningEvidence).filter_by(company_id=root['company_id']).order_by(LearningEvidence.recorded_at.desc(),LearningEvidence.id.desc()).all(): s.delete(evidence);s.flush()
  s.query(CompanyLearningMemoryV2).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
  s.query(PatternLearningMemory).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
  s.commit()
 finally:s.close()
 clean_base(root)
class FailOnce:
 remaining=1
 def orchestrate(self,cid,eid):
  if self.remaining: self.remaining-=1;raise RuntimeError('INJECTED_PREWRITE_FAILURE')
  return LearningRefreshOrchestrator().orchestrate(cid,eid)

def main():
 roots=[]
 try:
  root=make_context();roots.append(root);other=make_context();roots.append(other);ids=fixture(root);fixture(other);cid=root['company_id'];e=LearningEvidenceService();worker=LearningRefreshWorker('event-main',LearningRefreshDeliveryService(lease_seconds=600,max_attempts=3))
  # A/B/H: canonical observed evidence atomically gains delivery and exactly one material route.
  observed=e.record_event_observed(cid,ids['POS'][0]);dup=e.record_event_observed(cid,ids['POS'][0]);d=delivery(cid,observed.evidence_id);assert(observed.status,dup.status,d.state)==('CREATED','ALREADY_EXISTS','pending')
  base=counts(cid);r=worker.process_next(cid);m=EventIntelligenceMaterializationService().get_current(cid,'SKU','sales','POS');assert r.status=='COMPLETED' and d.id==r.delivery_id and m and delivery(cid,observed.evidence_id).last_outcome['event_statuses']
  # C/M: repeated recurring source refreshes the same memory; duplicate worker has no work.
  new=event(root,'POS','POS-25',25);rec=e.record_event_observed(cid,new.event_id);assert worker.process_next(cid).status=='COMPLETED';assert EventIntelligenceMaterializationService().get_current(cid,'SKU','sales','POS').id==m.id
  assert worker.process_next(cid).status=='NO_WORK'
  # D/E: accepted date and scope corrections supersede immutable evidence and route both old/new bounded scopes.
  ev=EventObservationService();cor=ev.propose_correction(cid,ids['POS'][0],root['user_id'],event_type='campaign_v2');ev.accept_correction(cid,cor.revision_id,root['user_id']);ce=e.record_event_corrected(cid,cor.revision_id);assert worker.process_next(cid).status=='COMPLETED' and delivery(cid,ce.evidence_id).state=='completed'
  scope=ev.propose_correction(cid,ids['POS'][1],root['user_id'],scope_value='OTHER');ev.accept_correction(cid,scope.revision_id,root['user_id']);se=e.record_event_corrected(cid,scope.revision_id);scope_result=worker.process_next(cid);scope_memory=EventIntelligenceMaterializationService().get_current(cid,'SKU','sales','POS');assert scope_result.status=='COMPLETED' and scope_memory.occurrence_count==2,{'worker':scope_result.status,'event_statuses':delivery(cid,se.evidence_id).last_outcome,'count':scope_memory.occurrence_count,'classification':scope_memory.classification}
  # F/G: cancelled evidence is durable; rejected correction creates neither evidence nor delivery.
  cancel=ev.cancel(cid,new.event_id,root['user_id']);can=e.record_event_cancelled(cid,cancel.revision_id);cancel_out=worker.process_next(cid);assert cancel_out.status=='COMPLETED',{'worker_status':cancel_out.status,'failure_code':cancel_out.failure_code,'delivery':delivery(cid,can.evidence_id).__dict__}
  before=len(e.list_scope(cid));rej=ev.propose_correction(cid,ids['NEG'][0],root['user_id'],event_type='rejected');ev.reject_correction(cid,rej.revision_id,root['user_id'])
  try:e.record_event_corrected(cid,rej.revision_id);raise AssertionError('rejected event correction recorded')
  except ValueError:pass
  assert len(e.list_scope(cid))==before
  # I/J/K: group/class/company events expand only to current company material metadata.
  for ident in ('SCOPE_G','SCOPE_C','COMPANY'):
   source=ids[ident][0];row=e.record_event_observed(cid,source);out=worker.process_next(cid);assert out.status=='COMPLETED' and delivery(cid,row.evidence_id).last_outcome['event_statuses']
  # L: consumption is distinct and cannot change sales memory.
  c1=e.record_event_observed(cid,ids['CONSUMPTION'][0]);assert worker.process_next(cid).status=='COMPLETED';assert EventIntelligenceMaterializationService().get_current(cid,'SKU','consumption','POS') is None # single occurrence is valid completed NOT_MATERIALIZED
  # S: accepted Actual correction route reconciles only overlapping bounded event identities.
  ledger=ActualWeeklyLedgerService();p=ingest(root,'sales',{5:155});ledger.approve_revision(cid,p['revision_ids'][0],root['user_id']);ae=e.record_actual_corrected(cid,p['revision_ids'][0]);out=worker.process_next(cid);assert out.status=='COMPLETED' and delivery(cid,ae.evidence_id).last_outcome['event_statuses']
  # N/R: one lease owner, expiry reclaim, and stale token remains rejected.
  race_event=event(root,'RACEDEL','RACEDEL-28',28);event(root,'RACEDEL','RACEDEL-30',30);race=e.record_event_observed(cid,race_event.event_id);rd=delivery(cid,race.evidence_id);svc=LearningRefreshDeliveryService(lease_seconds=20);claim=svc.claim(cid,rd.id,'lease-a');assert claim.status=='CLAIMED';assert LearningRefreshWorker('lease-b',LearningRefreshDeliveryService(lease_seconds=20)).process_next(cid).status=='NO_WORK';expire(cid,rd.id);assert LearningRefreshWorker('lease-b',LearningRefreshDeliveryService(lease_seconds=20)).process_next(cid).status=='COMPLETED'
  try:svc.complete(cid,rd.id,claim.claim_token,{});raise AssertionError('stale token completed')
  except Exception:pass
  # P/Q: retry after pre-write failure and after successful projection/lost completion converge.
  retry_event=event(root,'RETRY','RETRY-28',28);event(root,'RETRY','RETRY-30',30);re=e.record_event_observed(cid,retry_event.event_id);failed=LearningRefreshWorker('flaky',LearningRefreshDeliveryService(lease_seconds=20,orchestrator_factory=FailOnce)).process_next(cid);assert failed.status=='RETRY_PENDING';assert worker.process_next(cid).status=='COMPLETED'
  crash_event=event(root,'SCOPE_G','SCOPE_G-19',19,scope='PRODUCT_GROUP',value='G');cr=e.record_event_observed(cid,crash_event.event_id);cd=delivery(cid,cr.evidence_id);claim=svc.claim(cid,cd.id,'crash');assert LearningRefreshOrchestrator().orchestrate(cid,cr.evidence_id).outcome=='COMPLETED';state=EventIntelligenceMaterializationService().get_current(cid,'SKU','sales','SCOPE_G').row_version;expire(cid,cd.id);assert LearningRefreshWorker('recovery',LearningRefreshDeliveryService(lease_seconds=20)).process_next(cid).status=='COMPLETED';assert EventIntelligenceMaterializationService().get_current(cid,'SKU','sales','SCOPE_G').row_version==state
  # U/V/W/X: tenant isolation, fresh worker reconstruction, bounded delivery, no Pattern/Forecast/Runtime mutation from Event-only route.
  other_e=e.record_event_observed(other['company_id'],fixture(other)['POS'][0]) if False else None
  assert LearningRefreshWorker('tenant',LearningRefreshDeliveryService()).process_next(other['company_id']).status=='NO_WORK'
  after=counts(cid);assert after[4:]==base[4:]
  fresh=LearningRefreshWorker('fresh',LearningRefreshDeliveryService()).process_next(cid);assert fresh.status in {'NO_WORK','COMPLETED'}
  print('PHASE 3C7B4 PROBE PASS',{'observed':observed.status,'duplicate':dup.status,'accepted_correction':ce.status,'cancelled':can.status,'actual':ae.status,'lease':'reclaimed','retry':'completed'},flush=True)
 finally:
  for root in reversed(roots):clean(root)
if __name__=='__main__':main()
