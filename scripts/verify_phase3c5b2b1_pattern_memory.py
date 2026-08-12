"""Focused PostgreSQL proof for durable current Pattern Learning Memory."""
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.learning_evidence import LearningEvidenceService
from app.application.pattern_intelligence import PatternIntelligenceService
from app.application.pattern_learning_materialization import PatternLearningMaterializationService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.company import Company
from app.models.learning_evidence import LearningEvidence
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.runtime import RuntimeExecution
from app.models.retraining_job import RetrainingJob
from app.models.model_artifact import ModelArtifact
from app.models.champion_registry import ChampionRegistryCurrent
from app.models.learning import CompanyLearningMemory,PatternIntelligence,KnowledgeMaturity
from scripts.support.pattern_intelligence_fixture import create,cleanup

def calc(f,cutoff=None):
 s=SessionLocal()
 try:return PatternIntelligenceService(s).calculate(f.company_id,f.material_code,f.demand_type,cutoff or f.periods[-1])
 finally:s.close()
def count(cid):
 s=SessionLocal()
 try:return {'actual':s.query(ActualWeeklyObservation).filter_by(company_id=cid).count(),'revisions':s.query(ActualWeeklyRevision).filter_by(company_id=cid).count(),'evidence':s.query(LearningEvidence).filter_by(company_id=cid).count(),'memory':s.query(PatternLearningMemory).filter_by(company_id=cid).count(),'runtime':s.query(RuntimeExecution).filter_by(company_id=cid).count(),'jobs':s.query(RetrainingJob).filter_by(company_id=cid).count(),'artifacts':s.query(ModelArtifact).filter_by(company_id=cid).count(),'registry':s.query(ChampionRegistryCurrent).filter_by(company_id=cid).count(),'company_learning':s.query(CompanyLearningMemory).filter_by(company_id=cid).count()}
 finally:s.close()
def clear(f):
 s=SessionLocal()
 try:s.query(PatternLearningMemory).filter_by(company_id=f.company_id).delete(synchronize_session=False);s.query(LearningEvidence).filter_by(company_id=f.company_id).delete(synchronize_session=False);s.commit()
 finally:s.close()
def main():
 roots=[]
 try:
  stable=create('stable');roots.append(stable);ctx={'company_id':stable.company_id,'user_id':stable.user_id,'dataset_id':stable.dataset_id}
  trend=create('trend','TREND','sales','finished_good',ctx);volatile=create('volatile','VOL','sales','finished_good',ctx);inter=create('intermittent','SPARSE','consumption','raw_material',ctx);lumpy=create('lumpy','LUMP','sales','finished_good',ctx);semi=create('stable','SEMI','sales','semi_finished_good',ctx);short=create('insufficient','SHORT','sales','finished_good',ctx)
  other=create('stable');roots.append(other);svc=PatternLearningMaterializationService()
  # Establish compact LearningEvidence lineage from an authoritative source.
  s=SessionLocal();obs=s.query(ActualWeeklyObservation).filter_by(company_id=stable.company_id,material_code=stable.material_code,demand_type='sales',period=stable.periods[-1]).one().id;s.close();LearningEvidenceService().record_actual_accepted(stable.company_id,obs)
  before=count(stable.company_id);first=svc.materialize(stable.company_id,stable.material_code,'sales',stable.periods[-1]);same=svc.materialize(stable.company_id,stable.material_code,'sales',stable.periods[-1]);assert (first.status,same.status,first.row_version,same.row_version)==('CREATED','UNCHANGED',1,1)
  assert all(svc.materialize(stable.company_id,f.material_code,f.demand_type,f.periods[-1]).status=='CREATED' for f in (trend,volatile,inter,lumpy,semi))
  assert svc.materialize(stable.company_id,short.material_code,'sales',short.periods[-1]).status=='NOT_MATERIALIZED'
  memory=svc.get_current(stable.company_id,stable.material_code,'sales');assert memory.source_learning_evidence_ids and memory.pattern_classification=='STABLE'
  # Same-cutoff later Actual is ignored; later cutoff advances exactly once.
  ledger=ActualWeeklyLedgerService();ledger.ingest_dataset_actuals(stable.company_id,stable.user_id,stable.dataset_id,[{'material_code':stable.material_code,'period':'2026-W13','quantity':999,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');assert svc.materialize(stable.company_id,stable.material_code,'sales','2026-W12').status=='UNCHANGED';later=svc.materialize(stable.company_id,stable.material_code,'sales','2026-W13');assert later.status=='UPDATED' and later.row_version==2
  # An accepted correction updates; a rejected correction does not.
  p=ledger.ingest_dataset_actuals(stable.company_id,stable.user_id,stable.dataset_id,[{'material_code':stable.material_code,'period':'2026-W12','quantity':180,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');ledger.approve_revision(stable.company_id,p['revision_ids'][0],stable.user_id);updated=svc.materialize(stable.company_id,stable.material_code,'sales','2026-W13');assert updated.status=='UPDATED' and updated.row_version==3
  p=ledger.ingest_dataset_actuals(stable.company_id,stable.user_id,stable.dataset_id,[{'material_code':stable.material_code,'period':'2026-W12','quantity':190,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');ledger.reject_revision(stable.company_id,p['revision_ids'][0],stable.user_id);assert svc.materialize(stable.company_id,stable.material_code,'sales','2026-W13').status=='UNCHANGED'
  # A real concurrent same-scope request converges through PostgreSQL uniqueness/lock.
  race=create('trend');roots.append(race);barrier=threading.Barrier(2)
  def contender():barrier.wait();return PatternLearningMaterializationService().materialize(race.company_id,race.material_code,'sales',race.periods[-1])
  with ThreadPoolExecutor(max_workers=2) as pool: outcomes=list(pool.map(lambda _:contender(),range(2)))
  assert sorted(x.status for x in outcomes)==['CREATED','UNCHANGED']
  # A previously calculated W12 result cannot overwrite the newer W13 projection.
  stale=calc(stable,'2026-W12');s=SessionLocal()
  try: stale_result=PatternLearningMaterializationService()._persist(s,stale)
  finally:s.close()
  assert stale_result.status=='STALE_RESULT' and svc.get_current(stable.company_id,stable.material_code,'sales').cutoff_period=='2026-W13'
  sales=svc.get_current(stable.company_id,'SPARSE','consumption');assert sales.demand_type=='consumption' and svc.get_current(other.company_id,stable.material_code,'sales') is None
  fresh=PatternLearningMaterializationService().get_current(stable.company_id,trend.material_code,'sales');assert fresh and fresh.pattern_classification in {'TRENDING','STRUCTURAL_CHANGE'}
  after=count(stable.company_id);assert after['runtime']==before['runtime']==0 and after['jobs']==before['jobs']==0 and after['artifacts']==before['artifacts']==0 and after['registry']==before['registry']==0 and after['company_learning']==before['company_learning']==0
  print('PHASE3C5B2B1 PASS',{'stable':first.status,'unchanged':same.status,'later':later.status,'accepted_correction':updated.status,'rejected':'UNCHANGED','concurrency':sorted(x.status for x in outcomes),'stale':stale_result.status,'memory_rows':after['memory']},flush=True)
 finally:
  for f in reversed(roots):clear(f);cleanup(f)
  s=SessionLocal()
  try:assert all(s.query(Company).filter_by(id=f.company_id).count()==0 for f in roots)
  finally:s.close()
if __name__=='__main__':main()
