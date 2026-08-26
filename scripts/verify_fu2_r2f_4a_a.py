"""Minimal, read-only R2F-4A-A accepted-state recovery audit."""
import json
import sys
from pathlib import Path
from uuid import UUID
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.models import ActualWeeklyObservation as Actual, ActualWeeklyRevision as Revision, Dataset, DatasetVersion

manifest = json.loads(Path('scripts/verify_fu2_r2f_tenant_isolation.json').read_text())
company_id = UUID(manifest['owners'][0]['company_id'])
dataset_id = UUID(manifest['datasets'][0])
version_id = UUID(manifest['versions'][0])
session = SessionLocal()
try:
    dataset = session.query(Dataset).filter_by(id=dataset_id, company_id=company_id).one()
    assert session.query(DatasetVersion).filter_by(dataset_id=dataset_id).count() == 1
    assert session.query(DatasetVersion).filter_by(id=version_id, dataset_id=dataset_id).count() == 1
    actuals = session.query(Actual).filter_by(company_id=company_id).all()
    keys = [(row.company_id, row.material_code, row.demand_type, row.period) for row in actuals]
    assert len(keys) == len(set(keys))
    revisions = session.query(Revision).filter_by(company_id=company_id, source_dataset_id=dataset_id).all()
    assert revisions and all(row.approval_status == 'accepted' for row in revisions)
    assert len({row.id for row in revisions}) == len(revisions)
    print({'dataset_id':str(dataset.id),'actual_count':len(actuals),'actuals':[(x.material_code,x.demand_type,x.product_level,x.period,float(x.quantity)) for x in actuals],'revision_count':len(revisions),'revision_statuses':[x.approval_status for x in revisions],'revision_source_dataset_ids':[str(x.source_dataset_id) for x in revisions]}, flush=True)
finally:
    session.close()
print('FU2_R2F_4A_A_ACCEPTED_STATE_COMPLETE', flush=True)
