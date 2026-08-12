import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from xgboost.core import XGBoostError
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.database import SessionLocal
from scripts.support.rollback_xgboost_fixture import create_invalid_destination_matrix,cleanup_matrix
def main():
 matrix=None;s=None
 try:
  matrix=create_invalid_destination_matrix();s=SessionLocal();svc=XGBoostChallengerArtifactService(s)
  for scope in (matrix['primary'],matrix['raw']):svc.load(scope['company_id'],scope['artifact_b_id']);svc.load(scope['company_id'],scope['artifact_c_id'])
  try:svc.load(matrix['primary']['company_id'],matrix['primary']['invalid_artifact_id']);raise AssertionError('invalid native bytes loaded')
  except XGBoostError:pass
  p=matrix['primary'];assert matrix['other_tenant']['company_id']!=p['company_id'] and matrix['other_material']['company_id']==p['company_id'] and matrix['other_material']['material_code']!='MATERIAL_A' and matrix['other_demand']['company_id']==p['company_id'] and matrix['other_demand']['demand_type']=='consumption' and matrix['raw']['product_level']=='raw_material'
  print('PHASE3C3B3B2 R2B FIXTURE PASS',{'companies':len(matrix['company_ids']),'invalid_artifact_id':str(p['invalid_artifact_id']),'raw_artifact_id':str(matrix['raw']['artifact_b_id'])})
 finally:
  if s:s.close()
  if matrix:cleanup_matrix(matrix)
if __name__=='__main__':main()
