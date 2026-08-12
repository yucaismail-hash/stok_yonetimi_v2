"""Read-only recursive weekly XGBoost Champion inference."""
from dataclasses import dataclass
from math import cos,pi,sin
from statistics import pstdev
from app.application.champion_resolver import ChampionResolver
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.application.xgboost_weekly_features import FEATURE_NAMES,FEATURE_SCHEMA_VERSION,XGBoostWeeklyFeatureBuilder
from app.database import SessionLocal
from app.services.dataset.weekly_normalization import parse_weekly_period

INFERENCE_STRATEGY_VERSION='recursive_weekly_v1'
_LEVEL={'finished_good':0.0,'semi_finished_good':1.0,'raw_material':2.0};_DEMAND={'sales':0.0,'shipment':1.0,'order':2.0,'consumption':3.0,'other':4.0}
@dataclass(frozen=True)
class XGBoostChampionPrediction:
 company_id:object;material_code:str;demand_type:str;forecast_cutoff_period:str;target_periods:tuple;forecast_values:tuple;champion_registry_entry_id:object;model_artifact_id:object;model_used:str;xgboost_version:str;feature_schema_version:str;encoding_contract_version:str;inference_strategy_version:str;training_cutoff_period:str;artifact_checksum:str;recursive_input_counts:tuple
class XGBoostChampionInferenceService:
 def __init__(self,session_factory=SessionLocal,resolver=None,artifact_service_factory=None):self._session_factory=session_factory;self._resolver=resolver or ChampionResolver(session_factory);self._artifact_service_factory=artifact_service_factory
 def predict(self,company_id,material_code,demand_type,forecast_cutoff_period,forecast_horizon):
  resolution=self._resolver.resolve(company_id,material_code,demand_type,forecast_cutoff_period)
  if resolution.kind!='XGBOOST_ARTIFACT':raise ValueError('CHAMPION_NOT_XGBOOST')
  s=self._session_factory()
  try:
   features=XGBoostWeeklyFeatureBuilder(s).future_inference(company_id,material_code,demand_type,forecast_cutoff_period,forecast_horizon)
   if features is None:raise ValueError('NOT_PREDICTABLE')
   artifacts=self._artifact_service_factory(s) if self._artifact_service_factory else XGBoostChallengerArtifactService(s);artifact=artifacts.get(company_id,resolution.model_artifact_id)
   if artifact.feature_schema_version!=FEATURE_SCHEMA_VERSION:raise ValueError('ARTIFACT_FEATURE_SCHEMA_INCOMPATIBLE')
   model=artifacts.load(company_id,artifact.id);history=list(features['history']);values=[];counts=[]
   for target in features['target_periods']:
    last4=history[-4:];last8=history[-8:];week=parse_weekly_period(target).week
    row=(history[-1],history[-2],history[-3],history[-4],sum(last4)/4,pstdev(last4),sum(last8)/8,pstdev(last8),float(week),sin(2*pi*week/53),cos(2*pi*week/53),float(len(history)),_LEVEL[features['product_level']],_DEMAND[demand_type])
    value=float(model.predict([row])[0]);history.append(value);values.append(value);counts.append(len(history)-1)
   return XGBoostChampionPrediction(company_id,material_code,demand_type,forecast_cutoff_period,features['target_periods'],tuple(values),resolution.registry_entry_id,artifact.id,'xgboost',artifact.xgboost_version,artifact.feature_schema_version,artifact.encoding_contract_version,INFERENCE_STRATEGY_VERSION,artifact.training_cutoff_period,artifact.artifact_checksum,tuple(counts))
  finally:s.close()
