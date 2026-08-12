"""PostgreSQL proof for read-only ChampionResolver scope and fallback behavior."""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import xgboost
from sqlalchemy import update
from uuid_extensions import uuid7
from app.analysis.forecast import DemandForecaster
from app.application.champion_promotion import ChampionPromotionService
from app.application.champion_registry import ChampionRegistryService
from app.application.champion_resolver import ChampionResolver
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.application.xgboost_weekly_features import FEATURE_SCHEMA_VERSION
from app.database import SessionLocal
from app.engine.adapters.forecast_adapter import forecast_adapter
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_registry import Capability
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company, User
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.runtime import RuntimeResultReference
from app.services.model_artifact_storage import LocalModelArtifactStorage

def snapshot(s, cid):
 return (s.query(ChampionRegistryEntry).filter_by(company_id=cid).count(),s.query(ChampionRegistryTransition).filter_by(company_id=cid).count(),s.query(ChampionRegistryCurrent).filter_by(company_id=cid).count(),s.query(ModelArtifact).filter_by(company_id=cid).count(),s.query(ChampionChallengerDecision).filter_by(company_id=cid).count(),s.query(ActualWeeklyObservation).filter_by(company_id=cid).count(),s.query(ActualWeeklyRevision).filter_by(company_id=cid).count(),s.query(ForecastVintage).filter_by(company_id=cid).count(),s.query(ForecastEvaluation).filter_by(company_id=cid).count(),s.query(RuntimeResultReference).filter_by(company_id=cid).count(),s.query(CompanyLearningMemory).filter_by(company_id=cid).count(),s.query(UserLearningData).filter_by(company_id=cid).count())

def main():
 s=SessionLocal(); cid=uid=other=None; refs=[]; store=LocalModelArtifactStorage(Path(__file__).resolve().parents[1]/'.phase3c3b3a_resolver_artifacts')
 try:
  token='resolver_'+str(uuid7()); c=Company(id=uuid7(),name=token,tax_id=token); u=User(id=uuid7(),company_id=c.id,email=token+'@x.invalid',hashed_password='x'); b=Company(id=uuid7(),name=token+'b',tax_id=token+'b'); s.add_all((c,u,b));s.commit();cid,uid,other=c.id,u.id,b.id
  def artifact(code,demand,cutoff='2026-W32'):
   aid=uuid7(); booster=xgboost.Booster();booster.set_param({'num_feature':14,'objective':'reg:squarederror'});payload=bytes(booster.save_raw(raw_format='ubj'));ref=store.write(cid,aid,payload);refs.append(ref);a=ModelArtifact(id=aid,company_id=cid,material_code=code,demand_type=demand,model_role='challenger',model_family='xgboost',model_version='fixture-v1',artifact_contract_version='1',xgboost_version=xgboost.__version__,feature_schema_version=FEATURE_SCHEMA_VERSION,encoding_contract_version='explicit_category_codes_v1',split_policy_version='time_ordered_holdout_v1',training_cutoff_period=cutoff,training_period_start='2026-W09',training_period_end='2026-W28',validation_period_start='2026-W29',validation_period_end=cutoff,training_sample_count=20,validation_sample_count=4,seed=1,model_parameters={},artifact_storage_reference=ref,artifact_checksum=hashlib.sha256(payload).hexdigest(),artifact_size_bytes=len(payload),source_actual_observation_ids=[],source_evidence_signature='a'*64,artifact_fingerprint=hashlib.sha256(str(aid).encode()).hexdigest());s.add(a);s.flush();return a
  def promoted(code,demand,level,cutoff='2026-W32'):
   a=artifact(code,demand,cutoff);d=ChampionChallengerDecision(company_id=cid,material_code=code,demand_type=demand,challenger_model_artifact_id=a.id,champion_evidence={'product_metadata':{'product_level':level}},comparison_start_period='2026-W33',comparison_end_period='2026-W37',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision='PROMOTE_CHALLENGER',reason_codes=[],comparison_fingerprint=hashlib.sha256(str(a.id).encode()).hexdigest());s.add(d);s.commit();current=ChampionRegistryService().bootstrap(cid,code,demand,level);out=ChampionPromotionService(artifact_service_factory=lambda q:XGBoostChallengerArtifactService(q,store)).promote(cid,d.id,current.active_entry_id,current.row_version);assert out.status=='PROMOTED';return a,d,out.active_entry_id,current.active_entry_id
  resolver=ChampionResolver(artifact_service_factory=lambda q:XGBoostChallengerArtifactService(q,store))
  classical=ChampionRegistryService().bootstrap(cid,'CLASSICAL','sales','semi_finished_good');r=resolver.resolve(cid,'CLASSICAL','sales','2026-W32');assert r.kind=='CLASSICAL_EXISTING' and r.registry_entry_id==classical.active_entry_id and not r.fallback
  good,_,good_entry,good_classical=promoted('SKU','sales','finished_good');valid=resolver.resolve(cid,'SKU','sales','2026-W32');assert valid.kind=='XGBOOST_ARTIFACT' and valid.registry_entry_id==good_entry and valid.model_artifact_id==good.id and valid.artifact_checksum==good.artifact_checksum and valid.feature_schema_version==FEATURE_SCHEMA_VERSION
  raw,_,raw_entry,raw_classical=promoted('SKU','consumption','raw_material');consumption=resolver.resolve(cid,'SKU','consumption','2026-W32');assert consumption.kind=='XGBOOST_ARTIFACT' and consumption.registry_entry_id==raw_entry and consumption.model_artifact_id==raw.id
  corrupt,_,corrupt_entry,corrupt_classical=promoted('CORRUPT','sales','finished_good');before=snapshot(s,cid);(store.base_directory/corrupt.artifact_storage_reference).write_bytes(b'corrupt');fallback=resolver.resolve(cid,'CORRUPT','sales','2026-W32');assert fallback.kind=='CLASSICAL_EXISTING' and fallback.fallback and fallback.registry_entry_id==corrupt_classical and 'ARTIFACT_INTEGRITY' in fallback.reason_code and ChampionRegistryService().get_current(cid,'CORRUPT','sales').active_entry_id==corrupt_entry and snapshot(s,cid)==before
  missing,_,missing_entry,missing_classical=promoted('MISSING','sales','finished_good');store.delete_for_controlled_cleanup(missing.artifact_storage_reference);fallback_missing=resolver.resolve(cid,'MISSING','sales','2026-W32');assert fallback_missing.fallback and fallback_missing.registry_entry_id==missing_classical and 'ARTIFACT' in fallback_missing.reason_code and ChampionRegistryService().get_current(cid,'MISSING','sales').active_entry_id==missing_entry
  incompatible,_,_,incompatible_classical=promoted('INCOMPATIBLE','sales','finished_good');s.execute(update(ModelArtifact).where(ModelArtifact.id==incompatible.id).values(feature_schema_version='unsupported_fixture_v0'));s.commit();fallback_incompatible=resolver.resolve(cid,'INCOMPATIBLE','sales','2026-W32');assert fallback_incompatible.fallback and fallback_incompatible.registry_entry_id==incompatible_classical and 'INCOMPATIBLE' in fallback_incompatible.reason_code
  future,_,_,future_classical=promoted('FUTURE','sales','finished_good','2026-W35');cutoff_fallback=resolver.resolve(cid,'FUTURE','sales','2026-W32');assert cutoff_fallback.fallback and cutoff_fallback.registry_entry_id==future_classical and cutoff_fallback.reason_code=='ARTIFACT_CUTOFF_INCOMPATIBLE'
  orphan=artifact('ORPHAN','sales'); entry=ChampionRegistryEntry(company_id=cid,material_code='ORPHAN',demand_type='sales',entry_type='xgboost_artifact',model_artifact_id=orphan.id,product_level='finished_good',provenance={});s.add(entry);s.flush();s.add(ChampionRegistryCurrent(company_id=cid,material_code='ORPHAN',demand_type='sales',active_entry_id=entry.id,row_version=1));s.commit();store.delete_for_controlled_cleanup(orphan.artifact_storage_reference)
  try: resolver.resolve(cid,'ORPHAN','sales','2026-W32');raise AssertionError('orphan resolved')
  except RuntimeError as exc: assert 'CHAMPION_RESOLUTION_FAILED' in str(exc)
  try: resolver.resolve(other,'SKU','sales','2026-W32');raise AssertionError('cross tenant registry access')
  except LookupError as exc: assert str(exc)=='CHAMPION_NOT_FOUND'
  try: XGBoostChallengerArtifactService(s,store).get(other,good.id);raise AssertionError('cross tenant artifact access')
  except LookupError as exc: assert str(exc)=='MODEL_ARTIFACT_NOT_FOUND'
  assert resolver.resolve(cid,'SKU','sales','2026-W32').registry_entry_id==good_entry and resolver.resolve(cid,'SKU','consumption','2026-W32').registry_entry_id==raw_entry
  s.close();s=SessionLocal();resolver=ChampionResolver(artifact_service_factory=lambda q:XGBoostChallengerArtifactService(q,store));assert resolver.resolve(cid,'CLASSICAL','sales','2026-W32')==r and resolver.resolve(cid,'SKU','sales','2026-W32')==valid and resolver.resolve(cid,'CORRUPT','sales','2026-W32')==fallback
  calls={'fit':0,'predict':0,'resolver':0};fit,predict=xgboost.XGBRegressor.fit,xgboost.XGBRegressor.predict;resolve=ChampionResolver.resolve
  xgboost.XGBRegressor.fit=lambda *a,**k:(calls.__setitem__('fit',calls['fit']+1),fit(*a,**k))[1];xgboost.XGBRegressor.predict=lambda *a,**k:(calls.__setitem__('predict',calls['predict']+1),predict(*a,**k))[1];ChampionResolver.resolve=lambda *a,**k:(calls.__setitem__('resolver',calls['resolver']+1),resolve(*a,**k))[1]
  try:
   request=CapabilityExecutionRequest(uuid7(),'resolver-non-impact','forecast',Capability.DEMAND_FORECAST,cid,uid,uuid7(),30,params={'horizon':2});normal=forecast_adapter(DemandForecaster,{'items':[{'material_code':'SKU','demand_history':list(range(10,30))}]},request);assert normal['items'][0]['model_used'] in {'holt_winters','arima','simple'}
  finally: xgboost.XGBRegressor.fit,xgboost.XGBRegressor.predict,ChampionResolver.resolve=fit,predict,resolve
  assert calls=={'fit':0,'predict':0,'resolver':0}
  print('PHASE 3C3B3A RESOLVER PASS',{'valid_entry':str(good_entry),'fallbacks':3,'cutoff':cutoff_fallback.reason_code,'xgboost':xgboost.__version__})
 finally:
  if s:
   s.rollback()
   if cid:
    s.query(ChampionRegistryCurrent).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter_by(company_id=cid).delete(synchronize_session=False)
    for ref in refs:store.delete_for_controlled_cleanup(ref)
    s.query(ModelArtifact).filter_by(company_id=cid).delete(synchronize_session=False);s.query(User).filter_by(id=uid).delete(synchronize_session=False);s.query(Company).filter(Company.id.in_((cid,other))).delete(synchronize_session=False);s.commit();assert s.query(Company).filter(Company.id.in_((cid,other))).count()==0
   s.close()
if __name__=='__main__':main()
