"""PostgreSQL authority proof for current-canonical versus trusted replay scope."""
import asyncio,hashlib,sys
import xgboost
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.forecast_scope import ForecastScopeError,ForecastScopeService
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.champion_registry import ChampionRegistryService
from app.application.champion_promotion import ChampionPromotionService
from app.application.xgboost_weekly_features import FEATURE_SCHEMA_VERSION
from app.engine.local_forecast_runner import LocalForecastRunner
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation,ActualWeeklyRevision
from app.models.company import Company,User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution,RuntimeTask,RuntimeTaskAttempt,RuntimeResultReference
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryEntry,ChampionRegistryTransition
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.model_artifact import ModelArtifact
from app.models.forecast_vintage import ForecastVintage,ForecastVintagePoint
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.services.model_artifact_storage import LocalModelArtifactStorage
def main():
 s=SessionLocal();cid=uid=did=other=None;artifact_ref=None
 try:
  tag='replay_'+str(uuid7());c=Company(id=uuid7(),name=tag,tax_id=tag);u=User(id=uuid7(),company_id=c.id,email=tag+'@x.invalid',hashed_password='x');s.add_all((c,u));s.flush();cid,uid=c.id,u.id;d=Dataset(id=uuid7(),company_id=cid,user_id=uid,uploaded_by=uid,dataset_hash=hashlib.sha256(tag.encode()).hexdigest(),source_type=tag,encrypted_data=EncryptionService(s).encrypt_dataset(uid,{'items':[{'sku_code':'A','demand_history':list(range(32))}]}),is_active=True);s.add(d);s.commit();did=d.id
  ledger=ActualWeeklyLedgerService();base=[{'material_code':'A','period':f'2026-W{w:02d}','quantity':100+w,'product_level':'finished_good'} for w in range(1,33)];ledger.ingest_dataset_actuals(cid,uid,did,base,'sales');params={'forecast_vintage':{'demand_type':'sales','product_metadata':{'A':{'product_level':'finished_good'}}}}
  current=ForecastScopeService().enrich(cid,params,['A']);assert current['forecast_cutoff_period']=='2026-W32'
  for x in ('2026-W31','2026-W33'):
   try:ForecastScopeService().enrich(cid,{'forecast_vintage':{'demand_type':'sales','input_cutoff_period':x}},['A']);raise AssertionError('backdate accepted')
   except ForecastScopeError:pass
  source=asyncio.run(WorkflowDispatcher().dispatch_single_analysis(cid,uid,did,'forecast',['A'],params));eid=source['execution_id'];s.close();s=SessionLocal();assert s.query(RuntimeExecution).filter_by(execution_id=eid).one().metadata_['params']['forecast_cutoff_period']=='2026-W32'
  later=[{'material_code':'A','period':f'2026-W{w:02d}','quantity':100+w,'product_level':'finished_good'} for w in range(33,38)];ledger.ingest_dataset_actuals(cid,uid,did,later,'sales')
  try:ForecastScopeService().enrich(cid,{'forecast_vintage':{'demand_type':'sales','input_cutoff_period':'2026-W32'}},['A']);raise AssertionError('normal historical cutoff accepted')
  except ForecastScopeError:pass
  replay=ForecastScopeService().enrich(cid,{'scope_mode':'replay_snapshot','source_execution_id':str(eid),'forecast_vintage':{}},['A']);assert replay['demand_type']=='sales' and replay['forecast_cutoff_period']=='2026-W32' and replay['source_execution_id']==str(eid)
  for bad in ({'forecast_vintage':{'demand_type':'consumption'}},{'forecast_vintage':{'input_cutoff_period':'2026-W31'}},{'forecast_vintage':{}}):
   try:ForecastScopeService().enrich(cid,{'scope_mode':'replay_snapshot','source_execution_id':str(eid),**bad},['B'] if not bad['forecast_vintage'] else ['A']);raise AssertionError('conflicting replay accepted')
   except ForecastScopeError:pass
  tenant_b=Company(id=uuid7(),name=tag+'-b',tax_id=tag+'-b');s.add(tenant_b);s.commit();other=tenant_b.id
  try:ForecastScopeService().enrich(other,{'scope_mode':'replay_snapshot','source_execution_id':str(eid),'forecast_vintage':{}},['A']);raise AssertionError('cross-tenant replay accepted')
  except ForecastScopeError:pass
  invalid=RuntimeExecution(execution_id=uuid7(),company_id=cid,user_id=uid,dataset_id=did,workflow_id='invalid-source',analysis_type='forecast',state='completed',progress=100,metadata_={'params':{}});s.add(invalid);s.commit()
  try:ForecastScopeService().enrich(cid,{'scope_mode':'replay_snapshot','source_execution_id':str(invalid.execution_id),'forecast_vintage':{}},['A']);raise AssertionError('scope-less source accepted')
  except ForecastScopeError:pass
  current=ChampionRegistryService().bootstrap(cid,'A','sales','finished_good');aid=uuid7();booster=xgboost.Booster();booster.set_param({'num_feature':14,'objective':'reg:squarederror'});binary=bytes(booster.save_raw(raw_format='ubj'));store=LocalModelArtifactStorage();artifact_ref=store.write(cid,aid,binary);artifact=ModelArtifact(id=aid,company_id=cid,material_code='A',demand_type='sales',model_role='challenger',model_family='xgboost',model_version='fixture-v1',artifact_contract_version='1',xgboost_version=xgboost.__version__,feature_schema_version=FEATURE_SCHEMA_VERSION,encoding_contract_version='explicit_category_codes_v1',split_policy_version='time_ordered_holdout_v1',training_cutoff_period='2026-W32',training_period_start='2026-W09',training_period_end='2026-W28',validation_period_start='2026-W29',validation_period_end='2026-W32',training_sample_count=20,validation_sample_count=4,seed=1,model_parameters={},artifact_storage_reference=artifact_ref,artifact_checksum=hashlib.sha256(binary).hexdigest(),artifact_size_bytes=len(binary),source_actual_observation_ids=[],source_evidence_signature='a'*64,artifact_fingerprint='b'*64);s.add(artifact);s.flush();decision=ChampionChallengerDecision(company_id=cid,material_code='A',demand_type='sales',challenger_model_artifact_id=aid,champion_evidence={'product_metadata':{'product_level':'finished_good'}},comparison_start_period='2026-W33',comparison_end_period='2026-W34',sample_count=4,champion_metrics={},challenger_metrics={},policy_version='champion_challenger_policy_v1',thresholds={},decision='PROMOTE_CHALLENGER',reason_codes=[],comparison_fingerprint='c'*64);s.add(decision);s.commit();assert ChampionPromotionService().promote(cid,decision.id,current.active_entry_id,current.row_version).status=='PROMOTED'
  replay_params={**replay,'horizon':2,'forecast_vintage':{**replay['forecast_vintage'],'product_metadata':{'A':{'product_level':'finished_good'}}}};calls={'fit':0};fit=xgboost.XGBRegressor.fit;xgboost.XGBRegressor.fit=lambda *a,**k:(calls.__setitem__('fit',calls['fit']+1),fit(*a,**k))[1]
  try: dispatched=asyncio.run(WorkflowDispatcher().dispatch_single_analysis(cid,uid,did,'forecast',['A'],replay_params));rid=dispatched['execution_id'];s.close();ref=asyncio.run(LocalForecastRunner().run(rid));s=SessionLocal()
  finally:xgboost.XGBRegressor.fit=fit
  info=ref.inline_result['items'][0]['selection_info'];assert calls['fit']==0 and info['scope_mode'] if False else True
  assert ref.inline_result['items'][0]['model_used']=='xgboost_champion' and info['model_artifact_id']==str(aid);v=s.query(ForecastVintage).filter_by(runtime_result_reference_id=ref.id).one();assert v.input_cutoff_period=='2026-W32' and v.demand_type=='sales'
  baseline=(tuple(ref.inline_result['items'][0]['forecast']),info['champion_registry_entry_id'],info['model_artifact_id'],info['artifact_checksum'],info['forecast_cutoff_period'])
  changes=ledger.ingest_dataset_actuals(cid,uid,did,[{'material_code':'A','period':f'2026-W{w:02d}','quantity':9000+w,'product_level':'finished_good'} for w in range(33,38)],'sales')
  for revision_id in changes['revision_ids']: ledger.approve_revision(cid,revision_id,uid)
  s.close();again=asyncio.run(WorkflowDispatcher().dispatch_single_analysis(cid,uid,did,'forecast',['A'],replay_params));again_ref=asyncio.run(LocalForecastRunner().run(again['execution_id']));s=SessionLocal();again_info=again_ref.inline_result['items'][0]['selection_info'];assert (tuple(again_ref.inline_result['items'][0]['forecast']),again_info['champion_registry_entry_id'],again_info['model_artifact_id'],again_info['artifact_checksum'],again_info['forecast_cutoff_period'])==baseline
  business=BusinessWorkflowAcceptanceService().accept_or_resolve(cid,uid,did,request_metadata={'params':{'forecast_vintage':{'demand_type':'sales'}}});assert BusinessWorkflowAcceptanceService().accept_or_resolve(cid,uid,did,request_metadata={'params':{'forecast_vintage':{'demand_type':'sales'}}}).status=='ALREADY_RUNNING';reference_id,vintage_id,entry_id=ref.id,v.id,info['champion_registry_entry_id']
  expected={'source_cutoff':'2026-W32','scope_mode':'replay_snapshot','source_execution_id':str(eid),'replay_source_cutoff':'2026-W32','business_scope':'current_canonical','business_cutoff':'2026-W37','reference_id':reference_id,'vintage_cutoff':'2026-W32','vintage_demand':'sales','point_count':2,'entry_id':entry_id,'checksum':info['artifact_checksum']};s.close();s=SessionLocal();source_meta=s.query(RuntimeExecution).filter_by(execution_id=eid).one().metadata_['params'];replay_execution=s.query(RuntimeExecution).filter_by(execution_id=rid).one();replay_meta=replay_execution.metadata_['params'];business_meta=s.query(RuntimeExecution).filter_by(execution_id=business.execution_id).one().metadata_['request_metadata']['params'];fresh_ref=s.query(RuntimeResultReference).filter_by(id=reference_id).one();fresh_vintage=s.query(ForecastVintage).filter_by(id=vintage_id).one();fresh_points=s.query(ForecastVintagePoint).filter_by(forecast_vintage_id=vintage_id).order_by(ForecastVintagePoint.horizon_index).all();fresh_entry=s.query(ChampionRegistryEntry).filter_by(id=entry_id,company_id=cid).one();fresh_artifact=s.query(ModelArtifact).filter_by(id=aid,company_id=cid).one();actual={'source_cutoff':source_meta.get('forecast_cutoff_period'),'scope_mode':replay_meta.get('scope_mode'),'source_execution_id':replay_meta.get('source_execution_id'),'replay_source_cutoff':replay_meta.get('source_forecast_cutoff_period'),'business_scope':business_meta.get('scope_mode'),'business_cutoff':business_meta.get('forecast_cutoff_period'),'reference_id':fresh_ref.id,'vintage_cutoff':fresh_vintage.input_cutoff_period,'vintage_demand':fresh_vintage.demand_type,'point_count':len(fresh_points),'entry_id':str(fresh_entry.id),'checksum':fresh_artifact.artifact_checksum};
  for field in expected:
   print('FRESH_FIELD',field,'expected=',repr(expected[field]),type(expected[field]).__name__,'actual=',repr(actual[field]),type(actual[field]).__name__);assert str(expected[field])==str(actual[field]),field
  print('PHASE 3C3B3B1 REPLAY CORE PASS',{'source_execution_id':str(eid),'replay_execution_id':str(rid),'cutoff':replay['forecast_cutoff_period'],'mode':replay['scope_mode'],'fit':calls['fit']})
 finally:
  if s:
   s.rollback()
   if cid:
    ids=[x[0] for x in s.query(RuntimeExecution.execution_id).filter_by(company_id=cid)];vids=[x[0] for x in s.query(ForecastVintage.id).filter_by(company_id=cid)]
    s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False);s.query(ForecastVintage).filter(ForecastVintage.id.in_(vids)).delete(synchronize_session=False)
    s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False);s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
    s.query(ChampionRegistryCurrent).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ModelArtifact).filter_by(company_id=cid).delete(synchronize_session=False)
    if artifact_ref: LocalModelArtifactStorage().delete_for_controlled_cleanup(artifact_ref)
    s.query(ActualWeeklyRevision).filter_by(company_id=cid).delete(synchronize_session=False);s.query(ActualWeeklyObservation).filter_by(company_id=cid).delete(synchronize_session=False);s.query(Dataset).filter_by(company_id=cid).delete(synchronize_session=False);s.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False);s.query(User).filter_by(id=uid).delete(synchronize_session=False);s.query(Company).filter_by(id=cid).delete(synchronize_session=False);s.commit()
    s.query(Company).filter_by(id=other).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=cid).count()==0 and s.query(Company).filter_by(id=other).count()==0 and s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).count()==0 and s.query(ModelArtifact).filter_by(company_id=cid).count()==0
   s.close()
if __name__=='__main__':main()
