"""Read-only final A/B FU2 R2F persisted integrity audit."""
import json, sys
from pathlib import Path
from uuid import UUID
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.models import ActualWeeklyObservation as A,ActualWeeklyRevision as R,Dataset,DatasetVersion as V,RuntimeExecution,ForecastVintage,DecisionSnapshot
from app.models.workflow import WorkflowExecution
m=json.loads(Path('scripts/verify_fu2_r2f_tenant_isolation.json').read_text()); cs=[UUID(x['company_id']) for x in m['owners']]; ds=[UUID(x) for x in m['datasets']]; vs=[UUID(x) for x in m['versions']]; vals={'2026-W01':101.0,'2026-W02':102.0,'2026-W03':103.0,'2026-W04':104.0}
s=SessionLocal()
try:
 before=(s.query(Dataset).filter(Dataset.id.in_(ds)).count(),s.query(V).filter(V.dataset_id.in_(ds)).count(),s.query(A).filter(A.company_id.in_(cs)).count(),s.query(R).filter(R.company_id.in_(cs)).count())
 d=[s.query(Dataset).filter_by(id=ds[i],company_id=cs[i]).one() for i in range(2)];assert d[0].id!=d[1].id and d[0].dataset_hash!=d[1].dataset_hash
 for i in range(2):
  assert s.query(V).filter_by(dataset_id=ds[i]).count()==1 and s.query(V).filter_by(id=vs[i],dataset_id=ds[i]).count()==1
  assert s.query(V).join(Dataset).filter(V.id==vs[i],Dataset.company_id==cs[1-i]).one_or_none() is None
  rows=s.query(A).filter_by(company_id=cs[i],material_code='SKU-FU2-R2F',demand_type='sales').all();assert {x.period:float(x.quantity) for x in rows}==vals and all(x.product_level=='finished_good' for x in rows);assert len({(x.company_id,x.material_code,x.demand_type,x.period) for x in rows})==4
  rev=s.query(R).filter_by(company_id=cs[i],source_dataset_id=ds[i],approval_status='accepted').all();assert len(rev)==4 and all(x.source_dataset_id==ds[i] for x in rev) and len({x.id for x in rev})==4
  assert s.query(A).filter(A.company_id==cs[1-i],A.id.in_([x.id for x in rows])).count()==0
  assert s.query(RuntimeExecution).filter_by(company_id=cs[i]).count()==0 and s.query(ForecastVintage).filter_by(company_id=cs[i]).count()==0 and s.query(DecisionSnapshot).filter_by(company_id=cs[i]).count()==0
 after=(s.query(Dataset).filter(Dataset.id.in_(ds)).count(),s.query(V).filter(V.dataset_id.in_(ds)).count(),s.query(A).filter(A.company_id.in_(cs)).count(),s.query(R).filter(R.company_id.in_(cs)).count());assert before==after
finally:s.close()
print('FU2_R2F_FINAL_AB_AUDIT_COMPLETE',flush=True)
