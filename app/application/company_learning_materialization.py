"""Read-only aggregation into the canonical Company Learning V2 projection."""
from dataclasses import dataclass
from datetime import datetime,timezone
from hashlib import sha256
import json
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.learning_evidence import LearningEvidence
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.forecast_evaluation import ForecastEvaluation,ForecastEvaluationPoint
from app.models.retraining_job import RetrainingJob
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry,ChampionRegistryTransition

POLICY='company_learning_memory_v2';SCORE_POLICY='company_evidence_maturity_v1'
@dataclass(frozen=True)
class CompanyLearningMaterializationResult: status:str;memory_id:object;row_version:int;source_summary_fingerprint:str
class CompanyLearningMaterializationService:
 def __init__(self,session_factory=SessionLocal):self._sf=session_factory
 def materialize(self,company_id):
  s=self._sf()
  try:return self._persist(s,self._snapshot(s,company_id))
  except IntegrityError:
   s.rollback();return self._recover(company_id)
  finally:s.close()
 def get_current(self,company_id):
  s=self._sf()
  try:return s.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).one_or_none()
  finally:s.close()
 def _snapshot(self,s,cid):
  evidence=s.query(LearningEvidence).filter_by(company_id=cid).all();patterns=s.query(PatternLearningMemory).filter_by(company_id=cid).all();evaluations=s.query(ForecastEvaluation).filter_by(company_id=cid).all();jobs=s.query(RetrainingJob).filter_by(company_id=cid).all();transitions=s.query(ChampionRegistryTransition).filter_by(company_id=cid).all();currents=s.query(ChampionRegistryCurrent).filter_by(company_id=cid).all();entries={x.id:x for x in s.query(ChampionRegistryEntry).filter_by(company_id=cid).all()}
  types={};
  for x in evidence:types[x.event_type]=types.get(x.event_type,0)+1
  distribution={};
  for x in patterns:distribution[x.pattern_classification]=distribution.get(x.pattern_classification,0)+1
  scopes={(x.material_code,x.demand_type) for x in patterns}|{(x.material_code,x.demand_type) for x in jobs}|{(x.material_code,x.demand_type) for x in transitions}
  fscopes={(p.material_code,e.demand_type) for e in evaluations for p in s.query(ForecastEvaluationPoint).filter_by(evaluation_id=e.id)}
  retraining={state:sum(j.state==state for j in jobs) for state in ('pending','queued','running','trained','not_trainable','failed')}
  champion={'promotion_count':sum(t.transition_type=='PROMOTION' for t in transitions),'rollback_count':sum(t.transition_type=='ROLLBACK' for t in transitions),'xgboost_current_scope_count':sum(entries.get(x.active_entry_id).entry_type=='xgboost_artifact' for x in currents if x.active_entry_id in entries),'classical_current_scope_count':sum(entries.get(x.active_entry_id).entry_type=='classical_existing' for x in currents if x.active_entry_id in entries)}
  dates=[x.recorded_at for x in evidence if x.recorded_at];diversity=sum(bool(v) for v in (evidence,patterns,evaluations,jobs,transitions));score=min(100,round(min(30,len(scopes)*10)+min(25,len(patterns)*10)+min(20,len(fscopes)*5)+min(15,diversity*3)+min(10,len(evidence)*2),3));level='HIGH' if score>=70 else 'MEDIUM' if score>=35 else 'LOW'
  semantic={'policy':POLICY,'score_policy':SCORE_POLICY,'evidence':sorted((str(x.id),x.evidence_fingerprint) for x in evidence),'patterns':sorted((str(x.id),x.source_pattern_fingerprint,x.row_version) for x in patterns),'evaluations':sorted((str(x.id),str(x.recalculated_at)) for x in evaluations),'jobs':sorted((str(x.id),x.state,str(x.model_artifact_id)) for x in jobs),'transitions':sorted((str(x.id),x.transition_type) for x in transitions),'current':sorted((str(x.id),str(x.active_entry_id),x.row_version) for x in currents)};fp=sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  return dict(company_id=cid,company_learning_policy_version=POLICY,learning_score_policy_version=SCORE_POLICY,evidence_count=len(evidence),evidence_type_counts=types,evidence_source_diversity=diversity,material_scope_count=len({x[0] for x in scopes}),demand_scope_count=len({x[1] for x in scopes}),pattern_memory_scope_count=len(patterns),forecast_evaluated_scope_count=len(fscopes),forecast_evaluation_sample_count=sum(x.evaluated_point_count for x in evaluations),pattern_distribution=distribution,accepted_correction_evidence_count=types.get('ACTUAL_CORRECTED',0),retraining_summary=retraining,champion_summary=champion,latest_evidence_at=max(dates) if dates else None,oldest_evidence_at=min(dates) if dates else None,evidence_maturity_score=score,evidence_maturity_level=level,source_summary_fingerprint=fp)
 def _persist(self,s,snap):
  current=s.query(CompanyLearningMemoryV2).filter_by(company_id=snap['company_id']).with_for_update().one_or_none()
  if current and current.source_summary_fingerprint==snap['source_summary_fingerprint']:return CompanyLearningMaterializationResult('UNCHANGED',current.id,current.row_version,current.source_summary_fingerprint)
  values={**snap,'last_materialized_at':datetime.now(timezone.utc)}
  if current:
   for k,v in values.items():setattr(current,k,v)
   current.row_version+=1;s.commit();return CompanyLearningMaterializationResult('UPDATED',current.id,current.row_version,current.source_summary_fingerprint)
  current=CompanyLearningMemoryV2(row_version=1,**values);s.add(current);s.commit();return CompanyLearningMaterializationResult('CREATED',current.id,1,current.source_summary_fingerprint)
 def persist_snapshot(self,snapshot):
  s=self._sf()
  try:
   current=s.query(CompanyLearningMemoryV2).filter_by(company_id=snapshot['company_id']).with_for_update().one_or_none()
   if current and current.source_summary_fingerprint!=snapshot['source_summary_fingerprint']:return CompanyLearningMaterializationResult('STALE_RESULT',current.id,current.row_version,current.source_summary_fingerprint)
   return self._persist(s,snapshot)
  finally:s.close()
 def _recover(self,cid):
  current=self.get_current(cid);return CompanyLearningMaterializationResult('UNCHANGED',current.id,current.row_version,current.source_summary_fingerprint)
