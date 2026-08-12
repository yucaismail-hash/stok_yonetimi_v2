"""Reusable persisted A -> B -> C XGBoost Champion rollback fixture."""
from dataclasses import dataclass
from uuid_extensions import uuid7
from app.application.champion_rollback import ChampionRollbackService
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.model_artifact import ModelArtifact
from app.services.model_artifact_storage import LocalModelArtifactStorage
import hashlib

@dataclass(frozen=True)
class RollbackFixtureIds:
 company_id: object; material_code: str; demand_type: str; entry_a_id: object; entry_b_id: object; entry_c_id: object; artifact_b_id: object; artifact_c_id: object; rollback_transition_id: object|None

def create(material_code='SKU', demand_type='sales', product_level='finished_good'):
 # Reuses the verified native-UBJ artifact + immutable decision/promotion path from R6.
 from scripts.verify_phase3c3b3b1_scope_r6_closeout import _artifact
 s=SessionLocal(); refs=[]
 try:
  tag='rollback_fixture_'+str(uuid7()); company=Company(id=uuid7(),name=tag,tax_id=tag);s.add(company);s.commit();cid=company.id
  bid=_artifact(s,cid,material_code,demand_type,product_level,refs); b=s.query(ChampionRegistryEntry).filter_by(company_id=cid,model_artifact_id=bid).one().id
  aid=s.query(ChampionRegistryTransition).filter_by(company_id=cid,transition_type='BOOTSTRAP').one().destination_entry_id
  cid_art=_artifact(s,cid,material_code,demand_type,product_level,refs); c=s.query(ChampionRegistryEntry).filter_by(company_id=cid,model_artifact_id=cid_art).one().id
  return RollbackFixtureIds(cid,material_code,demand_type,aid,b,c,bid,cid_art,None),tuple(refs)
 finally:s.close()

def cleanup(ids,refs):
 s=SessionLocal()
 try:
  s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).delete(synchronize_session=False);s.query(ModelArtifact).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
  for ref in refs:LocalModelArtifactStorage().delete_for_controlled_cleanup(ref)
  s.query(Company).filter_by(id=ids.company_id).delete(synchronize_session=False);s.commit();assert s.query(Company).filter_by(id=ids.company_id).count()==0
 finally:s.close()

def create_invalid_destination_matrix():
 """Returns primitive IDs for test-only rejected-destination scenarios."""
 from scripts.verify_phase3c3b3b1_scope_r6_closeout import _artifact
 s=SessionLocal(); refs=[]; companies=[]
 try:
  def company(label):
   c=Company(id=uuid7(),name='rollback_matrix_'+label+'_'+str(uuid7()),tax_id='rollback_matrix_'+label+'_'+str(uuid7()));s.add(c);s.commit();companies.append(c.id);return c.id
  def scope(cid,material,demand,level):
   bid=_artifact(s,cid,material,demand,level,refs);b=s.query(ChampionRegistryEntry).filter_by(company_id=cid,model_artifact_id=bid).one().id;cid_art=_artifact(s,cid,material,demand,level,refs);c=s.query(ChampionRegistryEntry).filter_by(company_id=cid,model_artifact_id=cid_art).one().id;return {'company_id':cid,'material_code':material,'demand_type':demand,'product_level':level,'entry_b_id':b,'entry_c_id':c,'artifact_b_id':bid,'artifact_c_id':cid_art}
  primary=scope(company('a'),'MATERIAL_A','sales','finished_good');other_tenant=scope(company('b'),'MATERIAL_A','sales','finished_good');other_material=scope(primary['company_id'],'MATERIAL_B','sales','finished_good');other_demand=scope(primary['company_id'],'MATERIAL_A','consumption','finished_good');raw=scope(company('raw'),'RAW','consumption','raw_material')
  # Checksum/size are deliberately valid; Booster load is the first failure point.
  payload=b'not-a-native-xgboost-model';aid=uuid7();ref=LocalModelArtifactStorage().write(primary['company_id'],aid,payload);refs.append(ref);artifact=ModelArtifact(id=aid,company_id=primary['company_id'],material_code='MATERIAL_A',demand_type='sales',model_role='challenger',model_family='xgboost',model_version='fixture-invalid',artifact_contract_version='1',xgboost_version='2.1.4',feature_schema_version='xgboost_weekly_v1',encoding_contract_version='explicit_category_codes_v1',split_policy_version='time_ordered_holdout_v1',training_cutoff_period='2026-W32',training_period_start='2026-W09',training_period_end='2026-W28',validation_period_start='2026-W29',validation_period_end='2026-W32',training_sample_count=20,validation_sample_count=4,seed=1,model_parameters={},artifact_storage_reference=ref,artifact_checksum=hashlib.sha256(payload).hexdigest(),artifact_size_bytes=len(payload),source_actual_observation_ids=[],source_evidence_signature='i'*64,artifact_fingerprint=hashlib.sha256((str(aid)+'invalid').encode()).hexdigest());s.add(artifact);s.flush();entry=ChampionRegistryEntry(company_id=primary['company_id'],material_code='MATERIAL_A',demand_type='sales',entry_type='xgboost_artifact',model_artifact_id=aid,product_level='finished_good',provenance={});s.add(entry);s.commit();primary.update({'invalid_artifact_id':aid,'invalid_entry_id':entry.id,'invalid_artifact_storage_reference':ref})
  return {'primary':primary,'other_tenant':other_tenant,'other_material':other_material,'other_demand':other_demand,'raw':raw,'company_ids':tuple(companies),'artifact_refs':tuple(refs)}
 finally:s.close()

def cleanup_matrix(matrix):
 s=SessionLocal()
 try:
  cids=matrix['company_ids'];s.query(ChampionRegistryCurrent).filter(ChampionRegistryCurrent.company_id.in_(cids)).delete(synchronize_session=False);s.query(ChampionRegistryTransition).filter(ChampionRegistryTransition.company_id.in_(cids)).delete(synchronize_session=False);s.query(ChampionRegistryEntry).filter(ChampionRegistryEntry.company_id.in_(cids)).delete(synchronize_session=False);s.query(ChampionChallengerDecision).filter(ChampionChallengerDecision.company_id.in_(cids)).delete(synchronize_session=False);s.query(ModelArtifact).filter(ModelArtifact.company_id.in_(cids)).delete(synchronize_session=False)
  for ref in matrix['artifact_refs']:LocalModelArtifactStorage().delete_for_controlled_cleanup(ref)
  s.query(Company).filter(Company.id.in_(cids)).delete(synchronize_session=False);s.commit();assert s.query(Company).filter(Company.id.in_(cids)).count()==0
 finally:s.close()
