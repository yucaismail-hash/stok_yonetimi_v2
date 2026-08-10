"""Cutoff-safe weekly training matrix from canonical accepted actuals only."""
from dataclasses import dataclass
from math import cos, pi, sin
from statistics import pstdev
from app.models.actuals import ActualWeeklyObservation
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period

FEATURE_SCHEMA_VERSION='xgboost_weekly_v1'
FEATURE_NAMES=('lag_1','lag_2','lag_3','lag_4','rolling_mean_4','rolling_std_4','rolling_mean_8','rolling_std_8','week_of_year','seasonal_sin','seasonal_cos','trend_index')
@dataclass(frozen=True)
class XGBoostWeeklyTrainingMatrix:
 material_code:str; demand_type:str; training_cutoff_period:str; feature_schema_version:str; feature_names:tuple[str,...]; X:tuple[tuple[float,...],...]; y:tuple[float,...]; target_periods:tuple[str,...]; product_level:str; product_group:str|None; product_class:str|None; source_actual_observation_ids:tuple[str,...]
class XGBoostWeeklyFeatureBuilder:
 def __init__(self,session): self.session=session
 def build(self,company_id,material_code,demand_type,training_cutoff_period):
  demand_type=validate_demand_type(demand_type); cutoff=parse_weekly_period(training_cutoff_period).period
  rows=self.session.query(ActualWeeklyObservation).filter_by(company_id=company_id,material_code=material_code,demand_type=demand_type).all();rows=sorted((r for r in rows if parse_weekly_period(r.period).period<=cutoff),key=lambda r:(parse_weekly_period(r.period).year,parse_weekly_period(r.period).week))
  X=[];y=[];periods=[];ids=[]
  for i,row in enumerate(rows):
   if i<8:continue
   history=[float(x.quantity) for x in rows[:i]];week=parse_weekly_period(row.period).week;last4=history[-4:];last8=history[-8:]
   X.append((history[-1],history[-2],history[-3],history[-4],sum(last4)/4,pstdev(last4),sum(last8)/8,pstdev(last8),float(week),sin(2*pi*week/53),cos(2*pi*week/53),float(i))) ;y.append(float(row.quantity));periods.append(row.period);ids.append(str(row.id))
  meta=rows[-1] if rows else None
  return XGBoostWeeklyTrainingMatrix(material_code,demand_type,cutoff,FEATURE_SCHEMA_VERSION,FEATURE_NAMES,tuple(X),tuple(y),tuple(periods),meta.product_level if meta else '',meta.product_group if meta else None,meta.product_class if meta else None,tuple(ids))
