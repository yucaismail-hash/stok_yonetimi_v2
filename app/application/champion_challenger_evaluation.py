import hashlib,json
from dataclasses import dataclass
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.services.dataset.weekly_normalization import parse_weekly_period
POLICY_VERSION='champion_challenger_policy_v1'; THRESHOLDS={'min_sample_count':4,'min_relative_wape_improvement':.10,'max_bias_regression':.05}
@dataclass(frozen=True)
class ChampionEvidence: company_id:object;material_code:str;demand_type:str;model_identity:str;model_version:str|None;start_period:str;end_period:str;sample_count:int;metrics:dict;source_evidence:dict
class ChampionChallengerEvaluationService:
 def __init__(self,session,artifact_service=None):self.session=session;self.artifacts=artifact_service or XGBoostChallengerArtifactService(session)
 def compare(self,champion,artifact_id,challenger_metrics):
  artifact=self.artifacts.get(champion.company_id,artifact_id); self.artifacts.load(champion.company_id,artifact_id)
  if artifact.material_code!=champion.material_code or artifact.demand_type!=champion.demand_type: raise ValueError('CHALLENGER_SCOPE_MISMATCH')
  if parse_weekly_period(champion.start_period).period<=parse_weekly_period(artifact.training_cutoff_period).period: raise ValueError('COMPARISON_WINDOW_NOT_OUT_OF_SAMPLE')
  payload={'champion':champion.source_evidence,'artifact':str(artifact.id),'metrics':challenger_metrics,'window':[champion.start_period,champion.end_period],'policy':POLICY_VERSION}; fp=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(); old=self.session.query(ChampionChallengerDecision).filter_by(company_id=champion.company_id,comparison_fingerprint=fp).one_or_none()
  if old:return old
  cw=float(champion.metrics['wape']);xw=float(challenger_metrics['wape']); cb=abs(float(champion.metrics['bias']));xb=abs(float(challenger_metrics['bias']))
  if champion.sample_count<THRESHOLDS['min_sample_count']: decision,reasons='INSUFFICIENT_EVIDENCE',['INSUFFICIENT_SAMPLE']
  elif xw>cw*(1-THRESHOLDS['min_relative_wape_improvement']): decision,reasons='KEEP_CHAMPION',['INSUFFICIENT_WAPE_IMPROVEMENT']
  elif xb>cb+THRESHOLDS['max_bias_regression']: decision,reasons='KEEP_CHAMPION',['BIAS_GUARDRAIL']
  elif float(challenger_metrics['mae'])>float(champion.metrics['mae'])*1.05: decision,reasons='KEEP_CHAMPION',['MAE_GUARDRAIL']
  elif float(challenger_metrics['rmse'])>float(champion.metrics['rmse'])*1.05: decision,reasons='KEEP_CHAMPION',['RMSE_GUARDRAIL']
  else: decision,reasons='PROMOTE_CHALLENGER',['MATERIAL_WAPE_IMPROVEMENT']
  row=ChampionChallengerDecision(company_id=champion.company_id,material_code=champion.material_code,demand_type=champion.demand_type,challenger_model_artifact_id=artifact.id,champion_evidence=champion.source_evidence,comparison_start_period=champion.start_period,comparison_end_period=champion.end_period,sample_count=champion.sample_count,champion_metrics=champion.metrics,challenger_metrics=challenger_metrics,policy_version=POLICY_VERSION,thresholds=THRESHOLDS,decision=decision,reason_codes=reasons,comparison_fingerprint=fp);self.session.add(row);self.session.flush();return row
