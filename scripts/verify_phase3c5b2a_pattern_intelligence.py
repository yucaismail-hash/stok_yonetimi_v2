"""Full PostgreSQL matrix for read-only Pattern Intelligence."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.pattern_intelligence import PatternIntelligenceService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry,ChampionRegistryTransition
from app.models.company import Company
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.learning import CompanyLearningMemory,PatternIntelligence,UserLearningData,KnowledgeMaturity
from app.models.learning_evidence import LearningEvidence
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from scripts.support.pattern_intelligence_fixture import create,cleanup

def calculate(fixture,cutoff=None):
 s=SessionLocal()
 try:return PatternIntelligenceService(s).calculate(fixture.company_id,fixture.material_code,fixture.demand_type,cutoff or fixture.periods[-1])
 finally:s.close()
def state(cid):
 s=SessionLocal()
 try:
  models=(ActualWeeklyObservation,ActualWeeklyRevision,LearningEvidence,RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference,RetrainingJob,ModelArtifact,ChampionRegistryEntry,ChampionRegistryCurrent,ChampionRegistryTransition,CompanyLearningMemory,UserLearningData,PatternIntelligence,KnowledgeMaturity)
  return tuple(s.query(m).filter_by(company_id=cid).count() if hasattr(m,'company_id') else 0 for m in models)
 finally:s.close()
def summary(row):
 return {'status':row.status,'classification':row.classification,'sample_count':row.sample_count,'mean':row.mean_demand,'std':row.std_demand,'cv':row.coefficient_of_variation,'zero_ratio':row.zero_demand_ratio,'adi':row.adi,'slope':row.trend_slope,'strength':row.trend_strength,'recent_change':row.recent_change_ratio,'coverage':row.coverage_ratio,'missing':len(row.missing_periods),'confidence':row.confidence}
def main():
 owned=[]
 try:
  stable=create('stable');owned.append(stable); trend=create('trend');owned.append(trend); volatile=create('volatile');owned.append(volatile); intermittent=create('intermittent');owned.append(intermittent); lumpy=create('lumpy');owned.append(lumpy); missing=create('missing');owned.append(missing); insufficient=create('insufficient');owned.append(insufficient)
  # Same company/material but isolated sales and consumption scopes.
  ctx={'company_id':stable.company_id,'user_id':stable.user_id,'dataset_id':stable.dataset_id}
  sales_same=create('trend','DUAL','sales','finished_good',ctx); consumption_same=create('intermittent','DUAL','consumption','raw_material',ctx)
  semi=create('stable','SEMI','sales','semi_finished_good');owned.append(semi); raw=create('stable','RAW','consumption','raw_material');owned.append(raw)
  before=state(stable.company_id)
  a,b,c,d,e,f,g=map(calculate,(stable,trend,volatile,intermittent,lumpy,missing,insufficient))
  print('PATTERN POLICY DIAGNOSTIC',{'stable':summary(a),'trend':summary(b),'volatile':summary(c),'intermittent':summary(d),'lumpy':summary(e)},flush=True)
  assert a.classification=='STABLE' and b.classification in {'TRENDING','STRUCTURAL_CHANGE'} and c.classification=='VOLATILE' and d.classification=='INTERMITTENT' and e.classification=='LUMPY'
  assert f.coverage_ratio<1 and len(f.missing_periods)==1 and g.status=='INSUFFICIENT_HISTORY' and g.confidence==0
  assert a.seasonality_status==b.seasonality_status=='SEASONALITY_NOT_ESTABLISHED'
  assert calculate(stable)==a and calculate(trend)==b
  # Same-cutoff post-history evidence is excluded.
  ledger=ActualWeeklyLedgerService(); cutoff=stable.periods[-1]
  ledger.ingest_dataset_actuals(stable.company_id,stable.user_id,stable.dataset_id,[{'material_code':stable.material_code,'period':'2026-W13','quantity':999,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');assert calculate(stable,cutoff)==a
  proposed=ledger.ingest_dataset_actuals(stable.company_id,stable.user_id,stable.dataset_id,[{'material_code':stable.material_code,'period':cutoff,'quantity':180,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');ledger.approve_revision(stable.company_id,proposed['revision_ids'][0],stable.user_id); corrected=calculate(stable,cutoff);assert corrected.source_fingerprint!=a.source_fingerprint
  proposed=ledger.ingest_dataset_actuals(stable.company_id,stable.user_id,stable.dataset_id,[{'material_code':stable.material_code,'period':cutoff,'quantity':190,'product_level':'finished_good','product_group':'G','product_class':'C'}],'sales');ledger.reject_revision(stable.company_id,proposed['revision_ids'][0],stable.user_id);assert calculate(stable,cutoff)==corrected
  sales,consumption=calculate(sales_same),calculate(consumption_same);assert sales.demand_type=='sales' and consumption.demand_type=='consumption' and sales.source_actual_observation_ids!=consumption.source_actual_observation_ids and sales.source_fingerprint!=consumption.source_fingerprint
  assert calculate(semi).product_level=='semi_finished_good' and calculate(raw).product_level=='raw_material'
  # Fresh service/session only uses persisted primitive scope.
  assert calculate(trend)==b and calculate(intermittent)==d
  after=state(stable.company_id);print('READ ONLY COUNTS',{'before':before,'after':after},flush=True);assert after[:2]==(before[0]+1,before[1]+3) and after[2:]==before[2:]
  print('PHASE3C5B2A PASS',{'stable':summary(a),'trend':summary(b),'volatile':summary(c),'intermittent':summary(d),'lumpy':summary(e),'missing':summary(f),'insufficient':summary(g),'corrected_fingerprint_changed':True,'read_only_non_actual_tables':True},flush=True)
 finally:
  for item in reversed(owned): cleanup(item)
  s=SessionLocal()
  try:assert all(s.query(Company).filter_by(id=item.company_id).count()==0 for item in owned)
  finally:s.close()
if __name__=='__main__':main()
