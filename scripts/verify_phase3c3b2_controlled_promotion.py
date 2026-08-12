"""Focused PostgreSQL proof for explicit registry promotion (no Forecast activation)."""
import asyncio, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.champion_promotion import ChampionPromotionService
from app.application.champion_registry import ChampionRegistryService
from app.application.xgboost_challenger_training import XGBoostChallengerTrainingRequest,XGBoostChallengerTrainingService
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.application.xgboost_challenger_artifacts import ArtifactIntegrityError
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry,ChampionRegistryTransition
from app.models.model_artifact import ModelArtifact
from app.models.company import Company
from app.services.model_artifact_storage import LocalModelArtifactStorage
from scripts.support.champion_evidence_fixture import create_finished_good_sales,cleanup

def main():
 storage=LocalModelArtifactStorage(Path(__file__).resolve().parents[1]/'.phase3c3b2_probe_artifacts'); ids=None; refs=[]; s=None
 def before(cid,uid,did):
  q=SessionLocal()
  try:
   req=XGBoostChallengerTrainingRequest(cid,'SKU','sales','2026-W32',{'tier':'TIER_3_DEEP_LEARN_RETRAIN'},seed=23); result=XGBoostChallengerTrainingService(q).train(req); assert result.status=='TRAINED'; art=XGBoostChallengerArtifactService(q,storage).persist(req,result).artifact; refs.append(art.artifact_storage_reference);q.commit()
  finally:q.close()
 try:
  ids,evidence,_=asyncio.run(create_finished_good_sales(before_forecast=before));s=SessionLocal(); art=s.query(ModelArtifact).filter_by(company_id=ids.company_id,material_code='SKU',demand_type='sales').one()
  decision=ChampionChallengerDecision(company_id=ids.company_id,material_code='SKU',demand_type='sales',challenger_model_artifact_id=art.id,champion_evidence={'product_metadata':{'product_level':'finished_good','product_group':'G','product_class':'C'}},comparison_start_period='2026-W34',comparison_end_period='2026-W37',sample_count=4,champion_metrics={'wape':.1,'bias':0,'mae':1,'rmse':1},challenger_metrics={'wape':.01,'bias':0,'mae':.1,'rmse':.1},policy_version='champion_challenger_policy_v1',thresholds={'min_sample_count':4},decision='PROMOTE_CHALLENGER',reason_codes=['fixture'],comparison_fingerprint='promotion-'+str(art.id));s.add(decision);s.commit()
  current=ChampionRegistryService().bootstrap(ids.company_id,'SKU','sales','finished_good','G','C'); p=ChampionPromotionService(artifact_service_factory=lambda session:XGBoostChallengerArtifactService(session,storage)); promoted=p.promote(ids.company_id,decision.id,current.active_entry_id,current.row_version); assert promoted.status=='PROMOTED'; repeat=p.promote(ids.company_id,decision.id,current.active_entry_id,current.row_version); assert repeat.status=='ALREADY_PROMOTED' and repeat.active_entry_id==promoted.active_entry_id
  # Invalid decisions cannot mutate the registry.
  for status in ('KEEP_CHAMPION','INSUFFICIENT_EVIDENCE'):
   d=ChampionChallengerDecision(company_id=ids.company_id,material_code='SKU',demand_type='sales',challenger_model_artifact_id=art.id,champion_evidence={},comparison_start_period='2026-W34',comparison_end_period='2026-W37',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision=status,reason_codes=[],comparison_fingerprint=status+str(art.id));s.add(d);s.commit();assert p.promote(ids.company_id,d.id,promoted.active_entry_id,2).status=='NOT_PROMOTABLE'
  # A valid decision evaluated against B becomes stale after controlled synthetic pointer movement to C.
  stale=ChampionChallengerDecision(company_id=ids.company_id,material_code='SKU',demand_type='sales',challenger_model_artifact_id=art.id,champion_evidence={},comparison_start_period='2026-W34',comparison_end_period='2026-W37',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision='PROMOTE_CHALLENGER',reason_codes=[],comparison_fingerprint='stale'+str(art.id));s.add(stale);s.commit(); c=ChampionRegistryEntry(company_id=ids.company_id,material_code='SKU',demand_type='sales',entry_type='classical_existing',classical_strategy='demand_forecaster_auto_v1',provenance={});s.add(c);s.flush(); pointer=s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code='SKU',demand_type='sales').one();pointer.active_entry_id=c.id;pointer.row_version=3;s.commit();assert p.promote(ids.company_id,stale.id,promoted.active_entry_id,2).status=='STALE_DECISION'
  other=Company(id=__import__('uuid_extensions').uuid7(),name='promotion_other_'+str(__import__('uuid_extensions').uuid7()),tax_id='promotion_other_'+str(__import__('uuid_extensions').uuid7()));s.add(other);s.commit();assert p.promote(other.id,decision.id,promoted.active_entry_id,2).status=='DECISION_NOT_FOUND';s.query(Company).filter_by(id=other.id).delete(synchronize_session=False);s.commit()
  corrupt=ChampionChallengerDecision(company_id=ids.company_id,material_code='SKU',demand_type='sales',challenger_model_artifact_id=art.id,champion_evidence={},comparison_start_period='2026-W34',comparison_end_period='2026-W37',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision='PROMOTE_CHALLENGER',reason_codes=[],comparison_fingerprint='corrupt'+str(art.id));s.add(corrupt);s.commit();before=(s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code='SKU',demand_type='sales').one().row_version,s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id,transition_type='PROMOTION').count());(storage.base_directory/art.artifact_storage_reference).write_bytes(b'corrupt');
  try:p.promote(ids.company_id,corrupt.id,c.id,3);raise AssertionError('corrupt artifact promoted')
  except ArtifactIntegrityError:pass
  after=(s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code='SKU',demand_type='sales').one().row_version,s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id,transition_type='PROMOTION').count());assert after==before
  artifact_id,decision_id=art.id,decision.id
  s.close();s=SessionLocal(); now=s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code='SKU',demand_type='sales').one(); dest=s.query(ChampionRegistryEntry).filter_by(id=promoted.active_entry_id).one(); trans=s.query(ChampionRegistryTransition).filter_by(id=promoted.transition_id).one(); assert now.row_version==3 and dest.entry_type=='xgboost_artifact' and dest.model_artifact_id==artifact_id and trans.source_decision_id==decision_id
  print('PHASE3C3B2 CORE PASS',{'status':promoted.status,'idempotent':repeat.status,'row_version':now.row_version})
 finally:
  if s:
   s.rollback()
   if ids:
    s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
    for ref in refs:storage.delete_for_controlled_cleanup(ref)
    s.query(ModelArtifact).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.commit();cleanup(s,ids)
   else:s.close()
if __name__=='__main__':main()
