"""Read-only Champion resolution; deliberately not wired into ForecastAdapter."""
from dataclasses import dataclass
from app.application.xgboost_challenger_artifacts import ArtifactIntegrityError,XGBoostChallengerArtifactService
from app.database import SessionLocal
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry
from app.services.dataset.weekly_normalization import parse_weekly_period

@dataclass(frozen=True)
class ChampionResolution:
 kind:str; registry_entry_id:object; model_artifact_id:object|None; fallback:bool=False; reason_code:str|None=None; artifact_checksum:str|None=None; feature_schema_version:str|None=None; training_cutoff_period:str|None=None

class ChampionResolver:
 def __init__(self,session_factory=SessionLocal,artifact_service_factory=None):self._session_factory=session_factory;self._artifact_service_factory=artifact_service_factory
 def resolve(self,company_id,material_code,demand_type,forecast_cutoff_period):
  cutoff=parse_weekly_period(forecast_cutoff_period).period;s=self._session_factory()
  try:
   current=s.query(ChampionRegistryCurrent).filter_by(company_id=company_id,material_code=material_code,demand_type=demand_type).one_or_none()
   if current is None: raise LookupError('CHAMPION_NOT_FOUND')
   entry=s.query(ChampionRegistryEntry).filter_by(id=current.active_entry_id,company_id=company_id,material_code=material_code,demand_type=demand_type).one_or_none()
   if entry is None: raise LookupError('CHAMPION_POINTER_INVALID')
   if entry.entry_type=='classical_existing':return ChampionResolution('CLASSICAL_EXISTING',entry.id,None)
   artifacts=self._artifact_service_factory(s) if self._artifact_service_factory else XGBoostChallengerArtifactService(s)
   try:
    artifact=artifacts.get(company_id,entry.model_artifact_id)
    if artifact.material_code!=material_code or artifact.demand_type!=demand_type:raise ValueError('ARTIFACT_SCOPE_MISMATCH')
    if parse_weekly_period(artifact.training_cutoff_period).period>cutoff:raise ValueError('ARTIFACT_CUTOFF_INCOMPATIBLE')
    artifacts.load(company_id,artifact.id)
    return ChampionResolution('XGBOOST_ARTIFACT',entry.id,artifact.id,False,None,artifact.artifact_checksum,artifact.feature_schema_version,artifact.training_cutoff_period)
   except (LookupError,ArtifactIntegrityError,ValueError) as exc:
    reason='ARTIFACT_MISSING_FALLBACK' if str(exc)=='artifact payload does not exist' else str(exc)
    fallback=s.query(ChampionRegistryEntry).filter_by(company_id=company_id,material_code=material_code,demand_type=demand_type,entry_type='classical_existing').order_by(ChampionRegistryEntry.created_at.desc()).first()
    if fallback:return ChampionResolution('CLASSICAL_EXISTING',fallback.id,None,True,reason)
    raise RuntimeError('CHAMPION_RESOLUTION_FAILED:'+reason)
  finally:s.close()
