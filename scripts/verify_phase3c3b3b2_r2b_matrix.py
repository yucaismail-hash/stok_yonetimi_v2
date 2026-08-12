import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.champion_rollback import ChampionRollbackService
from app.database import SessionLocal
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryTransition
from app.models.model_artifact import ModelArtifact
from app.services.model_artifact_storage import LocalModelArtifactStorage
from scripts.support.rollback_xgboost_fixture import create_invalid_destination_matrix,cleanup_matrix
def main():
 matrix=None;s=None
 try:
  matrix=create_invalid_destination_matrix();p=matrix['primary'];raw=matrix['raw'];svc=ChampionRollbackService()
  def state(scope):
   q=SessionLocal();c=q.query(ChampionRegistryCurrent).filter_by(company_id=scope['company_id'],material_code=scope['material_code'],demand_type=scope['demand_type']).one();n=q.query(ChampionRegistryTransition).filter_by(company_id=scope['company_id'],transition_type='ROLLBACK').count();q.close();return c.active_entry_id,c.row_version,n
  # Positive finished-good control.
  before=state(p);ok=svc.rollback(p['company_id'],p['material_code'],p['demand_type'],p['entry_c_id'],p['entry_b_id'],'valid xgboost control');assert ok.status=='ROLLED_BACK';assert state(p)==(p['entry_b_id'],before[1]+1,before[2]+1)
  # Restore C only as controlled fixture state; rejection cases never mutate it.
  s=SessionLocal();cur=s.query(ChampionRegistryCurrent).filter_by(company_id=p['company_id'],material_code=p['material_code'],demand_type=p['demand_type']).one();cur.active_entry_id=p['entry_c_id'];cur.row_version+=1;s.commit();s.close();s=None
  def rejected(destination,reason):
   before=state(p);r=svc.rollback(p['company_id'],p['material_code'],p['demand_type'],p['entry_c_id'],destination,reason);assert r.status=='INVALID_DESTINATION' and state(p)==before;return r.status
  # Checksum corruption reaches trusted integrity validation.
  s=SessionLocal();art=s.query(ModelArtifact).filter_by(id=p['artifact_b_id']).one();ref=art.artifact_storage_reference;LocalModelArtifactStorage().base_directory.joinpath(ref).write_bytes(b'corrupt');s.close();checksum=rejected(p['entry_b_id'],'checksum corrupt')
  invalid=rejected(p['invalid_entry_id'],'checksum valid invalid native bytes')
  s=SessionLocal();s.query(ModelArtifact).filter_by(id=p['invalid_artifact_id']).update({'feature_schema_version':'incompatible_fixture_v0'},synchronize_session=False);s.commit();s.close();schema=rejected(p['invalid_entry_id'],'schema incompatible')
  tenant=rejected(matrix['other_tenant']['entry_b_id'],'cross tenant');material=rejected(matrix['other_material']['entry_b_id'],'cross material');demand=rejected(matrix['other_demand']['entry_b_id'],'cross demand')
  raw_before=state(raw);raw_ok=svc.rollback(raw['company_id'],raw['material_code'],raw['demand_type'],raw['entry_c_id'],raw['entry_b_id'],'raw material control');assert raw_ok.status=='ROLLED_BACK' and state(raw)==(raw['entry_b_id'],raw_before[1]+1,raw_before[2]+1)
  s=SessionLocal();assert state(p)[0]==p['entry_c_id'];print('PHASE3C3B3B2 R2B MATRIX PASS',{'valid':ok.status,'raw':raw_ok.status,'rejections':[checksum,invalid,schema,tenant,material,demand],'primary_row_version':state(p)[1]})
 finally:
  if s:s.close()
  if matrix:cleanup_matrix(matrix)
if __name__=='__main__':main()
