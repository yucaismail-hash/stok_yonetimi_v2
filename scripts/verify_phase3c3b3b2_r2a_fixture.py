import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.application.champion_rollback import ChampionRollbackService
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.database import SessionLocal
from app.models.champion_registry import ChampionRegistryCurrent,ChampionRegistryTransition
from app.models.model_artifact import ModelArtifact
from scripts.support.rollback_xgboost_fixture import create,cleanup
def main():
 ids=refs=None
 try:
  ids,refs=create();s=SessionLocal();artifacts=XGBoostChallengerArtifactService(s);b=artifacts.get(ids.company_id,ids.artifact_b_id);c=artifacts.get(ids.company_id,ids.artifact_c_id);artifacts.load(ids.company_id,b.id);artifacts.load(ids.company_id,c.id);before=s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code=ids.material_code,demand_type=ids.demand_type).one();assert before.active_entry_id==ids.entry_c_id and before.row_version==3;s.close()
  result=ChampionRollbackService().rollback(ids.company_id,ids.material_code,ids.demand_type,ids.entry_c_id,ids.entry_b_id,'verified previous XGBoost B');assert result.status=='ROLLED_BACK'
  s=SessionLocal();current=s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code=ids.material_code,demand_type=ids.demand_type).one();rollback=s.query(ChampionRegistryTransition).filter_by(id=result.transition_id).one();assert current.active_entry_id==ids.entry_b_id and current.row_version==4 and rollback.transition_type=='ROLLBACK' and rollback.source_entry_id==ids.entry_c_id and rollback.destination_entry_id==ids.entry_b_id and s.query(ChampionRegistryTransition).filter_by(company_id=ids.company_id,transition_type='PROMOTION').count()==2;s.close()
  s=SessionLocal();fresh=s.query(ChampionRegistryCurrent).filter_by(company_id=ids.company_id,material_code=ids.material_code,demand_type=ids.demand_type).one();assert fresh.active_entry_id==ids.entry_b_id and s.query(ModelArtifact).filter_by(id=ids.artifact_b_id,company_id=ids.company_id).one().artifact_checksum==b.artifact_checksum;print('PHASE3C3B3B2 R2A PASS',{'company_id':str(ids.company_id),'entry_b_id':str(ids.entry_b_id),'entry_c_id':str(ids.entry_c_id),'artifact_b_id':str(ids.artifact_b_id),'artifact_c_id':str(ids.artifact_c_id),'row_version':fresh.row_version})
 finally:
  if 's' in locals():s.close()
  if ids:cleanup(ids,refs)
if __name__=='__main__':main()
