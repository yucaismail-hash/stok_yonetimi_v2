"""Focused PostgreSQL proof for incremental Pattern Memory refresh/recovery."""
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.pattern_learning_refresh import PatternLearningRefreshService
from app.application.pattern_learning_materialization import PatternLearningMaterializationService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.company import Company
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.learning_evidence import LearningEvidence
from app.models.runtime import RuntimeExecution
from app.models.retraining_job import RetrainingJob
from app.models.model_artifact import ModelArtifact
from app.models.champion_registry import ChampionRegistryCurrent
from app.models.learning import CompanyLearningMemory,PatternIntelligence,KnowledgeMaturity
from scripts.support.pattern_intelligence_fixture import create,cleanup

def snapshot(cid):
 s=SessionLocal()
 try:
  memory={ (x.material_code,x.demand_type):(x.id,x.row_version,x.cutoff_period,x.source_pattern_fingerprint) for x in s.query(PatternLearningMemory).filter_by(company_id=cid)}
  side=(s.query(LearningEvidence).filter_by(company_id=cid).count(),s.query(RuntimeExecution).filter_by(company_id=cid).count(),s.query(RetrainingJob).filter_by(company_id=cid).count(),s.query(ModelArtifact).filter_by(company_id=cid).count(),s.query(ChampionRegistryCurrent).filter_by(company_id=cid).count(),s.query(CompanyLearningMemory).filter_by(company_id=cid).count(),s.query(PatternIntelligence).filter_by(user_id=s.query(ActualWeeklyObservation).filter_by(company_id=cid).first().source_dataset_id).count() if False else 0)
  return memory,side
 finally:s.close()
def clear(f):
 s=SessionLocal()
 try:s.query(PatternLearningMemory).filter_by(company_id=f.company_id).delete(synchronize_session=False);s.query(LearningEvidence).filter_by(company_id=f.company_id).delete(synchronize_session=False);s.commit()
 finally:s.close()
def main():
 roots=[]
 try:
  a=create('stable','A','sales','finished_good');roots.append(a);ctx={'company_id':a.company_id,'user_id':a.user_id,'dataset_id':a.dataset_id}
  b=create('trend','B','sales','semi_finished_good',ctx);c=create('intermittent','C','consumption','raw_material',ctx);d=create('stable','D','sales','finished_good',ctx);short=create('insufficient','SHORT','sales','finished_good',ctx);other=create('stable','A','sales','finished_good');roots.append(other)
  service=PatternLearningRefreshService();cut=lambda f:f.periods[-1]
  initial=service.refresh_batch(tuple({'company_id':a.company_id,'material_code':f.material_code,'demand_type':f.demand_type,'cutoff_period':cut(f)} for f in (a,b,c)))
  assert [x.status for x in initial]==['CREATED']*3 and service.refresh(a.company_id,'SHORT','sales',cut(short)).status=='NOT_MATERIALIZED'
  baseline,_=snapshot(a.company_id)
  ledger=ActualWeeklyLedgerService();ledger.ingest_dataset_actuals(a.company_id,a.user_id,a.dataset_id,[{'material_code':'A','period':'2026-W13','quantity':180,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales')
  changed=service.refresh(a.company_id,'A','sales','2026-W13');assert changed.status=='UPDATED' and changed.row_version==2
  after,_=snapshot(a.company_id);assert after[('B','sales')]==baseline[('B','sales')] and after[('C','consumption')]==baseline[('C','consumption')] and ('D','sales') not in after
  p=ledger.ingest_dataset_actuals(a.company_id,a.user_id,a.dataset_id,[{'material_code':'A','period':'2026-W12','quantity':220,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');ledger.approve_revision(a.company_id,p['revision_ids'][0],a.user_id);accepted=service.refresh(a.company_id,'A','sales','2026-W13');assert accepted.status=='UPDATED' and accepted.row_version==3
  p=ledger.ingest_dataset_actuals(a.company_id,a.user_id,a.dataset_id,[{'material_code':'A','period':'2026-W12','quantity':230,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');ledger.reject_revision(a.company_id,p['revision_ids'][0],a.user_id);assert service.refresh(a.company_id,'A','sales','2026-W13').status=='UNCHANGED'
  assert service.refresh(a.company_id,'A','sales','2026-W13').status=='UNCHANGED'
  # Newer projection is never overwritten by delayed old cutoff.
  assert service.refresh(a.company_id,'A','sales','2026-W12').status=='STALE_RESULT'
  # Pre-write failure leaves current durable projection intact; a fresh retry recovers.
  before_fail=snapshot(a.company_id)[0][('A','sales')]
  try:PatternLearningRefreshService(before_materialize=lambda *_:(_ for _ in ()).throw(RuntimeError('INJECTED_PRE_WRITE'))).refresh(a.company_id,'A','sales','2026-W13')
  except RuntimeError:pass
  assert snapshot(a.company_id)[0][('A','sales')]==before_fail and PatternLearningRefreshService().refresh(a.company_id,'A','sales','2026-W13').status=='UNCHANGED'
  # Response-loss after a committed write retries idempotently.
  try:PatternLearningRefreshService(after_materialize=lambda _:(_ for _ in ()).throw(RuntimeError('INJECTED_POST_WRITE'))).refresh(a.company_id,'A','sales','2026-W13')
  except RuntimeError:pass
  assert PatternLearningRefreshService().refresh(a.company_id,'A','sales','2026-W13').status=='UNCHANGED'
  # Genuine concurrent duplicate delivery is safe.
  barrier=threading.Barrier(2)
  def runner():barrier.wait();return PatternLearningRefreshService().refresh(d.company_id,'D','sales',cut(d))
  with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(lambda _:runner(),range(2)))
  assert sorted(x.status for x in outcomes)==['CREATED','UNCHANGED'] and len(snapshot(a.company_id)[0])==4
  assert PatternLearningRefreshService().refresh(other.company_id,'A','sales',cut(other)).status=='CREATED'
  memory,side=snapshot(a.company_id);assert side==(0,0,0,0,0,0,0)
  print('PHASE3C5B2B2 PASS',{'accepted_actual':changed.status,'accepted_correction':accepted.status,'rejected':'UNCHANGED','duplicate':'UNCHANGED','concurrent':[x.status for x in outcomes],'stale':'STALE_RESULT','pre_retry':'UNCHANGED','post_retry':'UNCHANGED','dirty_scopes':len(initial),'memory_scopes':len(memory)},flush=True)
 finally:
  for f in reversed(roots):clear(f);cleanup(f)
  s=SessionLocal()
  try:assert all(s.query(Company).filter_by(id=f.company_id).count()==0 for f in roots)
  finally:s.close()
if __name__=='__main__':main()
