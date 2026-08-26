"""Minimal read-only R2F-4B accepted-state recovery audit."""
import json, sys
from pathlib import Path
from uuid import UUID
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.models import ActualWeeklyObservation as Actual, ActualWeeklyRevision as Revision, Dataset, DatasetVersion, RuntimeExecution, ForecastVintage, DecisionSnapshot
from app.models.workflow import WorkflowExecution
m=json.loads(Path('scripts/verify_fu2_r2f_tenant_isolation.json').read_text());ca,cb=UUID(m['owners'][0]['company_id']),UUID(m['owners'][1]['company_id']);da,db=UUID(m['datasets'][0]),UUID(m['datasets'][1]);va,vb=UUID(m['versions'][0]),UUID(m['versions'][1]);s=SessionLocal()
try:
 before=(s.query(DatasetVersion).filter_by(dataset_id=db).count(),s.query(Actual).filter_by(company_id=cb).count(),s.query(Revision).filter_by(company_id=cb).count())
 b=s.query(Dataset).filter_by(id=db,company_id=cb).one();a=s.query(Dataset).filter_by(id=da,company_id=ca).one();assert s.query(DatasetVersion).filter_by(dataset_id=db).count()==1 and s.query(DatasetVersion).filter_by(id=vb,dataset_id=db).count()==1 and va!=vb;assert s.query(DatasetVersion).filter_by(dataset_id=da).count()==1 and s.query(DatasetVersion).filter_by(id=va,dataset_id=da).count()==1
 rows=s.query(Actual).filter_by(company_id=cb,material_code='SKU-FU2-R2F',demand_type='sales').all();assert {x.period:float(x.quantity) for x in rows}=={'2026-W01':101.0,'2026-W02':102.0,'2026-W03':103.0,'2026-W04':104.0} and all(x.product_level=='finished_good' for x in rows);assert len({(x.company_id,x.material_code,x.demand_type,x.period) for x in rows})==4
 rev=s.query(Revision).filter_by(company_id=cb,source_dataset_id=db,approval_status='accepted').all();assert len(rev)==4 and len({x.id for x in rev})==4
 assert s.query(RuntimeExecution).filter_by(company_id=cb).count()==0 and s.query(ForecastVintage).filter_by(company_id=cb).count()==0 and s.query(DecisionSnapshot).filter_by(company_id=cb).count()==0;assert s.query(WorkflowExecution).filter_by(company_id=cb).count()==0 if hasattr(WorkflowExecution,'company_id') else True
 after=(s.query(DatasetVersion).filter_by(dataset_id=db).count(),s.query(Actual).filter_by(company_id=cb).count(),s.query(Revision).filter_by(company_id=cb).count());assert before==after
finally:s.close()
print('FU2_R2F_4B_ACCEPTED_STATE_COMPLETE',flush=True);print('FU2_R2F_ACCEPT_B_COMPLETE',flush=True)
