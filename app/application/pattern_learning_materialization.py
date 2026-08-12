"""Guarded current-projection materializer for read-only Pattern Intelligence."""
from dataclasses import dataclass
from datetime import datetime,timezone
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.application.pattern_intelligence import PatternIntelligenceService
from app.models.learning_evidence import LearningEvidence
from app.models.pattern_learning_memory import PatternLearningMemory
from app.services.dataset.weekly_normalization import parse_weekly_period

@dataclass(frozen=True)
class PatternMaterializationResult:
 status:str; memory_id:object|None; row_version:int|None; source_pattern_fingerprint:str|None
class PatternLearningMaterializationService:
 def __init__(self,session_factory=SessionLocal):self._session_factory=session_factory
 def materialize(self,company_id,material_code,demand_type,cutoff_period):
  session=self._session_factory()
  try:
   result=PatternIntelligenceService(session).calculate(company_id,material_code,demand_type,cutoff_period)
   if result.status!='OK':return PatternMaterializationResult('NOT_MATERIALIZED',None,None,result.source_fingerprint)
   return self._persist(session,result)
  except IntegrityError:
   session.rollback();return self._recover(company_id,material_code,demand_type,cutoff_period)
  except Exception:
   session.rollback();raise
  finally:session.close()
 def get_current(self,company_id,material_code,demand_type):
  s=self._session_factory()
  try:return s.query(PatternLearningMemory).filter_by(company_id=company_id,material_code=material_code,demand_type=demand_type).one_or_none()
  finally:s.close()
 def _persist(self,s,r):
  current=s.query(PatternLearningMemory).filter_by(company_id=r.company_id,material_code=r.material_code,demand_type=r.demand_type).with_for_update().one_or_none()
  if current and parse_weekly_period(r.cutoff_period).period<parse_weekly_period(current.cutoff_period).period:return PatternMaterializationResult('STALE_RESULT',current.id,current.row_version,current.source_pattern_fingerprint)
  lineage=[str(x[0]) for x in s.query(LearningEvidence.id).filter_by(company_id=r.company_id,material_code=r.material_code,demand_type=r.demand_type).order_by(LearningEvidence.recorded_at,LearningEvidence.id).all()]
  values=dict(product_level=r.product_level,product_group=r.product_group,product_class=r.product_class,pattern_classification=r.classification,pattern_policy_version=r.policy_version,feature_version=r.feature_version,confidence_policy_version=r.confidence_policy_version,sample_count=r.sample_count,period_start=r.first_period,period_end=r.last_period,cutoff_period=r.cutoff_period,coverage_ratio=r.coverage_ratio,missing_period_count=len(r.missing_periods),mean_demand=r.mean_demand,std_demand=r.std_demand,coefficient_of_variation=r.coefficient_of_variation,zero_demand_ratio=r.zero_demand_ratio,adi=r.adi,trend_slope=r.trend_slope,trend_strength=r.trend_strength,recent_change_ratio=r.recent_change_ratio,seasonality_status=r.seasonality_status,confidence=r.confidence,source_pattern_fingerprint=r.source_fingerprint,source_learning_evidence_ids=lineage,last_materialized_at=datetime.now(timezone.utc))
  if current:
   if current.source_pattern_fingerprint==r.source_fingerprint:return PatternMaterializationResult('UNCHANGED',current.id,current.row_version,current.source_pattern_fingerprint)
   for k,v in values.items():setattr(current,k,v)
   current.row_version+=1;s.commit();return PatternMaterializationResult('UPDATED',current.id,current.row_version,r.source_fingerprint)
  current=PatternLearningMemory(company_id=r.company_id,material_code=r.material_code,demand_type=r.demand_type,row_version=1,**values);s.add(current);s.commit();return PatternMaterializationResult('CREATED',current.id,1,r.source_fingerprint)
 def _recover(self,company_id,material_code,demand_type,cutoff):
  s=self._session_factory()
  try:
   current=s.query(PatternLearningMemory).filter_by(company_id=company_id,material_code=material_code,demand_type=demand_type).one()
   return PatternMaterializationResult('UNCHANGED' if current.cutoff_period==parse_weekly_period(cutoff).period else 'STALE_RESULT',current.id,current.row_version,current.source_pattern_fingerprint)
  finally:s.close()
