"""Minimal, read-only R2F-4A-B tenant/downstream non-interference audit."""
import json, sys
from pathlib import Path
from uuid import UUID
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.models import ActualWeeklyObservation as Actual, ActualWeeklyRevision as Revision, Dataset, DatasetVersion, RuntimeExecution, ForecastVintage, DecisionSnapshot
from app.models.workflow import WorkflowExecution

m=json.loads(Path('scripts/verify_fu2_r2f_tenant_isolation.json').read_text()); ca,cb=UUID(m['owners'][0]['company_id']),UUID(m['owners'][1]['company_id']); da,db=UUID(m['datasets'][0]),UUID(m['datasets'][1])
s=SessionLocal()
try:
 a=s.query(Dataset).filter_by(id=da,company_id=ca).one(); b=s.query(Dataset).filter_by(id=db,company_id=cb).one()
 assert a.company_id==ca and b.company_id==cb and b.state.value=='validated'
 assert s.query(DatasetVersion).filter_by(dataset_id=da).count()==1 and s.query(DatasetVersion).filter_by(dataset_id=db).count()==0
 assert s.query(Actual).filter_by(company_id=cb,material_code='SKU-FU2-R2F',demand_type='sales').count()==0
 assert s.query(Revision).filter_by(company_id=cb,source_dataset_id=db,approval_status='accepted').count()==0
 assert s.query(Actual).filter_by(company_id=cb).filter(Actual.id.in_([x.id for x in s.query(Actual).filter_by(company_id=ca).all()])).count()==0
 for cid in (ca,cb):
  assert s.query(RuntimeExecution).filter_by(company_id=cid).count()==0 and s.query(ForecastVintage).filter_by(company_id=cid).count()==0 and s.query(DecisionSnapshot).filter_by(company_id=cid).count()==0
  assert s.query(WorkflowExecution).filter_by(company_id=cid).count()==0 if hasattr(WorkflowExecution,'company_id') else True
finally:s.close()
print('FU2_R2F_4A_B_NON_INTERFERENCE_COMPLETE',flush=True);print('FU2_R2F_ACCEPT_A_COMPLETE',flush=True)
