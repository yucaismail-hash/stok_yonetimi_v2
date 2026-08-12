"""Focused PostgreSQL proof for durable authoritative Forecast scope."""
import asyncio, hashlib, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
import xgboost
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.forecast_scope import ForecastScopeError,ForecastScopeService
from app.application.champion_registry import ChampionRegistryService
from app.application.champion_promotion import ChampionPromotionService
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.application.xgboost_weekly_features import FEATURE_SCHEMA_VERSION
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.database import SessionLocal
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider
from app.engine.local_forecast_runner import LocalForecastRunner
from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry,ChampionRegistryTransition
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.model_artifact import ModelArtifact
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.services.model_artifact_storage import LocalModelArtifactStorage

def main():
 s=SessionLocal();cid=uid=did=None;artifact_ref=None
 try:
  tag='scope_'+str(uuid7());c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();cid,uid=c.id,u.id
  payload={'items':[{'sku_code':'SKU','demand_history':list(range(1,33))}]};d=Dataset(id=uuid7(),company_id=cid,user_id=uid,uploaded_by=uid,dataset_hash=hashlib.sha256(tag.encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(uid,payload),is_active=True);s.add(d);s.commit();did=d.id
  ledger=ActualWeeklyLedgerService();rows=[{'material_code':'SKU','period':f'2026-W{w:02d}','quantity':100+w,'product_level':'finished_good'} for w in range(1,33)];ledger.ingest_dataset_actuals(cid,uid,did,rows,'sales');ledger.ingest_dataset_actuals(cid,uid,did,[{**row,'quantity':200+w,'product_level':'raw_material'} for w,row in enumerate(rows,1)],'consumption')
  params={'horizon':2,'forecast_vintage':{'demand_type':'sales','product_metadata':{'SKU':{'product_level':'finished_good'}}}}
  classical=ChampionRegistryService().bootstrap(cid,'SKU','sales','finished_good');assert classical.active_entry_id
  scope=ForecastScopeService().enrich(cid,params,['SKU']);assert scope['demand_type']=='sales' and scope['forecast_cutoff_period']=='2026-W32' and scope['forecast_vintage']['input_cutoff_period']=='2026-W32'
  consumption=ForecastScopeService().enrich(cid,{'forecast_vintage':{'demand_type':'consumption'}},['SKU']);assert consumption['demand_type']=='consumption' and consumption['forecast_cutoff_period']=='2026-W32'
  for declared in ('2026-W31','2026-W33'):
   try:ForecastScopeService().enrich(cid,{'forecast_vintage':{'demand_type':'sales','input_cutoff_period':declared}},['SKU']);raise AssertionError('mismatch accepted')
   except ForecastScopeError:pass
  try:ForecastScopeService().enrich(cid,{'forecast_vintage':{}},['SKU']);raise AssertionError('missing demand accepted')
  except ForecastScopeError:pass
  dispatched=asyncio.run(WorkflowDispatcher().dispatch_single_analysis(cid,uid,did,'forecast',['SKU'],params));eid=dispatched['execution_id'];s.close();s=SessionLocal();execution=s.query(RuntimeExecution).filter_by(execution_id=eid,company_id=cid).one();persisted=execution.metadata_['params'];assert persisted['demand_type']=='sales' and persisted['forecast_cutoff_period']=='2026-W32'
  task=s.query(RuntimeTask).filter_by(execution_id=eid,company_id=cid).one();request=CapabilityExecutionRequest(eid,execution.workflow_id,task.task_id,Capability.DEMAND_FORECAST,cid,uid,did,300,material_codes=['SKU'],params=persisted);prepared=DatasetRuntimeProvider(s)(request);assert prepared['items'][0]['demand_type']=='sales' and prepared['items'][0]['forecast_cutoff_period']=='2026-W32'
  s.close();ref=asyncio.run(LocalForecastRunner().run(eid));s=SessionLocal();execution=s.query(RuntimeExecution).filter_by(execution_id=eid).one();result=ref.inline_result;item=result['items'][0];assert item['selection_info']['champion_resolution']=='classical_existing' and item['selection_info']['classical_strategy']=='demand_forecaster_auto_v1';vintage=s.query(ForecastVintage).filter_by(runtime_result_reference_id=ref.id).one();points=s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=vintage.id).all();assert vintage.demand_type==persisted['demand_type']=='sales' and vintage.input_cutoff_period==persisted['forecast_cutoff_period']=='2026-W32' and len(points)==2
  # Native persisted production artifact: no fit is used to build or execute this fixture.
  aid=uuid7();booster=xgboost.Booster();booster.set_param({'num_feature':14,'objective':'reg:squarederror'});binary=bytes(booster.save_raw(raw_format='ubj'));store=LocalModelArtifactStorage();artifact_ref=store.write(cid,aid,binary);artifact=ModelArtifact(id=aid,company_id=cid,material_code='SKU',demand_type='sales',model_role='challenger',model_family='xgboost',model_version='fixture-v1',artifact_contract_version='1',xgboost_version=xgboost.__version__,feature_schema_version=FEATURE_SCHEMA_VERSION,encoding_contract_version='explicit_category_codes_v1',split_policy_version='time_ordered_holdout_v1',training_cutoff_period='2026-W32',training_period_start='2026-W09',training_period_end='2026-W28',validation_period_start='2026-W29',validation_period_end='2026-W32',training_sample_count=20,validation_sample_count=4,seed=1,model_parameters={},artifact_storage_reference=artifact_ref,artifact_checksum=hashlib.sha256(binary).hexdigest(),artifact_size_bytes=len(binary),source_actual_observation_ids=[],source_evidence_signature='a'*64,artifact_fingerprint='b'*64);s.add(artifact);s.flush();decision=ChampionChallengerDecision(company_id=cid,material_code='SKU',demand_type='sales',challenger_model_artifact_id=aid,champion_evidence={'product_metadata':{'product_level':'finished_good'}},comparison_start_period='2026-W33',comparison_end_period='2026-W34',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision='PROMOTE_CHALLENGER',reason_codes=[],comparison_fingerprint='c'*64);s.add(decision);s.commit();current=ChampionRegistryService().get_current(cid,'SKU','sales');assert ChampionPromotionService().promote(cid,decision.id,current.active_entry_id,current.row_version).status=='PROMOTED'
  calls={'fit':0};original_fit=xgboost.XGBRegressor.fit;xgboost.XGBRegressor.fit=lambda *a,**k:(calls.__setitem__('fit',calls['fit']+1),original_fit(*a,**k))[1]
  try: xdispatch=asyncio.run(WorkflowDispatcher().dispatch_single_analysis(cid,uid,did,'forecast',['SKU'],params));xid=xdispatch['execution_id'];s.close();xref=asyncio.run(LocalForecastRunner().run(xid));s=SessionLocal()
  finally: xgboost.XGBRegressor.fit=original_fit
  xitem=xref.inline_result['items'][0];info=xitem['selection_info'];assert xitem['model_used']=='xgboost_champion' and info['champion_resolution']=='xgboost_artifact' and info['model_artifact_id']==str(aid) and info['demand_type']=='sales' and calls['fit']==0; xv=s.query(ForecastVintage).filter_by(runtime_result_reference_id=xref.id).one();assert xv.demand_type=='sales' and xv.input_cutoff_period=='2026-W32' and len(s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=xv.id).all())==2
  # Legacy direct adapter/provider shape remains unscoped unless callers request scope.
  assert DatasetRuntimeProvider(s)(CapabilityExecutionRequest(uuid7(),'legacy','forecast',Capability.DEMAND_FORECAST,cid,uid,did,300,material_codes=['SKU'],params={'horizon':2}))['items'][0].get('demand_type') is None
  print('PHASE 3C3B3B1-SCOPE CORE PASS',{'execution_id':str(eid),'xgboost_execution_id':str(xid),'sales_cutoff':persisted['forecast_cutoff_period'],'consumption_cutoff':consumption['forecast_cutoff_period'],'xgboost_fit':calls['fit']})
 finally:
  if s:
   s.rollback()
   if cid:
    ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid)];vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=cid)];s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter(ForecastVintage.id.in_(vids)).delete(synchronize_session=False);s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False);s.query(ChampionRegistryCurrent).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ModelArtifact).filter_by(company_id=cid).delete(synchronize_session=False);artifact_ref and LocalModelArtifactStorage().delete_for_controlled_cleanup(artifact_ref);s.query(ActualWeeklyRevision).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=cid).delete(synchronize_session=False);s.query(Dataset).filter_by(company_id=cid).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False);s.query(User).filter_by(id=uid).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit()
   s.close()
if __name__=='__main__':main()
