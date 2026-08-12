"""Lightweight persisted artifact/scope proof; no Forecast or XGBoost fit."""
import hashlib, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import xgboost
from uuid_extensions import uuid7
from app.application.champion_promotion import ChampionPromotionService
from app.application.champion_registry import ChampionRegistryService
from app.application.xgboost_challenger_artifacts import ArtifactIntegrityError,XGBoostChallengerArtifactService
from app.application.xgboost_weekly_features import FEATURE_SCHEMA_VERSION
from app.database import SessionLocal
from app.models.company import Company,User
from app.models.model_artifact import ModelArtifact
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry,ChampionRegistryTransition
from app.services.model_artifact_storage import LocalModelArtifactStorage

def main():
 started=time.perf_counter();s=SessionLocal();cid=uid=None;refs=[];storage=LocalModelArtifactStorage(Path(__file__).resolve().parents[1]/'.phase3c3b2_r4a_artifacts')
 def artifact(code,demand):
  aid=uuid7();booster=xgboost.Booster();booster.set_param({'num_feature':1,'objective':'reg:squarederror'});payload=bytes(booster.save_raw(raw_format='ubj'));ref=storage.write(cid,aid,payload);refs.append(ref);a=ModelArtifact(id=aid,company_id=cid,material_code=code,demand_type=demand,model_role='challenger',model_family='xgboost',model_version='1.0.0',artifact_contract_version='1.0.0',xgboost_version=xgboost.__version__,feature_schema_version=FEATURE_SCHEMA_VERSION,encoding_contract_version='explicit_category_codes_v1',split_policy_version='time_ordered_holdout_v1',training_cutoff_period='2026-W32',training_period_start='2026-W09',training_period_end='2026-W28',validation_period_start='2026-W29',validation_period_end='2026-W32',training_sample_count=20,validation_sample_count=4,seed=23,model_parameters={},artifact_storage_reference=ref,artifact_checksum=hashlib.sha256(payload).hexdigest(),artifact_size_bytes=len(payload),source_actual_observation_ids=[],source_evidence_signature=hashlib.sha256((code+demand).encode()).hexdigest(),artifact_fingerprint=hashlib.sha256((str(aid)).encode()).hexdigest());s.add(a);s.flush();return a
 def decision(a,code,demand,level,label):
  d=ChampionChallengerDecision(company_id=cid,material_code=code,demand_type=demand,challenger_model_artifact_id=a.id,champion_evidence={'product_metadata':{'product_level':level}},comparison_start_period='2026-W34',comparison_end_period='2026-W37',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision='PROMOTE_CHALLENGER',reason_codes=[],comparison_fingerprint=label+str(a.id));s.add(d);s.commit();return d
 try:
  token='r4a_'+str(uuid7());c=Company(id=uuid7(),name=token,tax_id=token);u=User(id=uuid7(),company_id=c.id,email=token+'@x.invalid',hashed_password='x');s.add_all((c,u));s.commit();cid,uid=c.id,u.id
  good=artifact('FG','sales');raw=artifact('RAW','consumption');bad=artifact('BAD','sales');s.commit();registry=ChampionRegistryService();service=ChampionPromotionService(artifact_service_factory=lambda q:XGBoostChallengerArtifactService(q,storage))
  fg=decision(good,'FG','sales','finished_good','fg');a=registry.bootstrap(cid,'FG','sales','finished_good');r=service.promote(cid,fg.id,a.active_entry_id,a.row_version);assert r.status=='PROMOTED'
  rd=decision(raw,'RAW','consumption','raw_material','raw');ra=registry.bootstrap(cid,'RAW','consumption','raw_material');rr=service.promote(cid,rd.id,ra.active_entry_id,ra.row_version);assert rr.status=='PROMOTED'
  # Same material, wrong demand decision/artifact must not promote consumption.
  cross=decision(good,'FG','consumption','finished_good','cross');ca=registry.bootstrap(cid,'FG','consumption','semi_finished_good');assert service.promote(cid,cross.id,ca.active_entry_id,ca.row_version).status=='ARTIFACT_SCOPE_MISMATCH'
  bd=decision(bad,'BAD','sales','finished_good','bad');ba=registry.bootstrap(cid,'BAD','sales','finished_good');before=(ba.active_entry_id,ba.row_version);(storage.base_directory/bad.artifact_storage_reference).write_bytes(b'corrupt')
  try:service.promote(cid,bd.id,ba.active_entry_id,ba.row_version);raise AssertionError('corrupt artifact promoted')
  except ArtifactIntegrityError:pass
  now=ChampionRegistryService().get_current(cid,'BAD','sales');assert (now.active_entry_id,now.row_version)==before and s.query(ChampionRegistryTransition).filter_by(company_id=cid,source_decision_id=bd.id,transition_type='PROMOTION').count()==0
  print('PHASE3C3B2-R4A PASS',{'fg':r.status,'raw':rr.status,'runtime_seconds':round(time.perf_counter()-started,3),'xgboost_fit':0,'forecast_calls':0})
 finally:
  if s:
   s.rollback()
   if cid:
    s.query(ChampionRegistryCurrent).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter_by(company_id=cid).delete(synchronize_session=False)
    for ref in refs:storage.delete_for_controlled_cleanup(ref)
    s.query(ModelArtifact).filter_by(company_id=cid).delete(synchronize_session=False);s.query(User).filter_by(id=uid).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit()
   s.close()
if __name__=='__main__':main()
