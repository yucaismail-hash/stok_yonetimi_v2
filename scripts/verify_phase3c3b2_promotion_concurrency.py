"""True PostgreSQL races for controlled Champion promotion."""
import asyncio, concurrent.futures, threading, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.champion_promotion import ChampionPromotionService
from app.application.champion_registry import ChampionRegistryService
from app.application.xgboost_challenger_training import XGBoostChallengerTrainingRequest,XGBoostChallengerTrainingService
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry,ChampionRegistryTransition
from app.models.model_artifact import ModelArtifact
from app.services.model_artifact_storage import LocalModelArtifactStorage
from scripts.support.champion_evidence_fixture import create_finished_good_sales,cleanup

def main():
 storage=LocalModelArtifactStorage(Path(__file__).resolve().parents[1]/'.phase3c3b2_r3_artifacts'); ids=None; refs=[]; s=None
 def before(cid,uid,did):
  q=SessionLocal()
  try:
   for cutoff in ('2026-W32','2026-W31'):
    req=XGBoostChallengerTrainingRequest(cid,'SKU','sales',cutoff,{'tier':'TIER_3_DEEP_LEARN_RETRAIN'},seed=23);r=XGBoostChallengerTrainingService(q).train(req);assert r.status=='TRAINED';a=XGBoostChallengerArtifactService(q,storage).persist(req,r).artifact;refs.append(a.artifact_storage_reference)
   q.commit()
  finally:q.close()
 def decision(s,cid,artifact,label):
  d=ChampionChallengerDecision(company_id=cid,material_code='SKU',demand_type='sales',challenger_model_artifact_id=artifact.id,champion_evidence={},comparison_start_period='2026-W34',comparison_end_period='2026-W37',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision='PROMOTE_CHALLENGER',reason_codes=[],comparison_fingerprint=label+str(artifact.id));s.add(d);s.commit();return d.id
 try:
  ids,_,_=asyncio.run(create_finished_good_sales(before_forecast=before));s=SessionLocal(); arts=s.query(ModelArtifact).filter_by(company_id=ids.company_id).order_by(ModelArtifact.training_cutoff_period.desc()).all();artifact_ids=[row.id for row in arts];d1=decision(s,ids.company_id,arts[0],'same');a=ChampionRegistryService().bootstrap(ids.company_id,'SKU','sales','finished_good');bar=threading.Barrier(2);svc=lambda:ChampionPromotionService(artifact_service_factory=lambda q:XGBoostChallengerArtifactService(q,storage))
  def call(d,entry,version):bar.wait();return svc().promote(ids.company_id,d,entry,version)
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex: same=list(ex.map(lambda _:call(d1,a.active_entry_id,a.row_version),range(2)))
  s.close();s=SessionLocal();cur=s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code='SKU',demand_type='sales').one();assert {x.status for x in same}=={'PROMOTED','ALREADY_PROMOTED'} and cur.row_version==2 and s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id,source_decision_id=d1,transition_type='PROMOTION').count()==1
  # Reset only registry state; immutable decisions/artifacts remain for a fresh competing scope.
  s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.commit();a=ChampionRegistryService().bootstrap(ids.company_id,'SKU','sales','finished_good');d2=decision(s,ids.company_id,s.query(ModelArtifact).filter_by(id=artifact_ids[1]).one(),'compete');bar=threading.Barrier(2)
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex: competing=list(ex.map(lambda value:call(value,a.active_entry_id,a.row_version),[d1,d2]))
  s.close();s=SessionLocal();cur=s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code='SKU',demand_type='sales').one();trans=s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id,transition_type='PROMOTION').all();assert sorted(x.status for x in competing)==['PROMOTED','STALE_DECISION'] and cur.row_version==2 and len(trans)==1
  print('PHASE3C3B2-R3 PASS',{'same':[x.status for x in same],'competing':[x.status for x in competing],'row_version':cur.row_version})
 finally:
  if s:
   s.rollback()
   if ids:
    s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
    for ref in refs:storage.delete_for_controlled_cleanup(ref)
    s.query(ModelArtifact).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.commit();cleanup(s,ids)
   else:s.close()
if __name__=='__main__':main()
