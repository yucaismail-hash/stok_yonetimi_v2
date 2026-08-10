"""PostgreSQL proof for the derived, no-hindsight Effective Forecast Timeline."""
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7
from app.application.effective_forecast_timeline import EffectiveForecastTimelineError, EffectiveForecastTimelineService, target_period_start
from app.database import SessionLocal
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt


def iso_time(period, hour=0):
    return target_period_start(period) + timedelta(hours=hour)


def counts(session, company_id):
    execution_ids = [value for value, in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id)]
    vintage_ids = [value for value, in session.query(ForecastVintage.id).filter_by(company_id=company_id)]
    return (
        session.query(ForecastVintage).filter_by(company_id=company_id).count(),
        session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).count(),
        session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).count(),
        session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(execution_ids)).count(),
    )


def add_vintage(session, company_id, user_id, dataset_id, label, available_at, cutoff, targets, demand_type='sales', product_group='legacy', learning=None):
    execution = RuntimeExecution(execution_id=uuid7(), company_id=company_id, user_id=user_id, dataset_id=dataset_id, workflow_id='phase3aa4_'+label, analysis_type='forecast', state='completed')
    session.add(execution); session.flush()
    reference = RuntimeResultReference(company_id=company_id, execution_id=execution.execution_id, result_type='forecast', result_version='1.0.0', contract_version='1.0.0', storage_kind='inline_jsonb', inline_result={'fixture':label}, validation_status='validated', created_at=available_at)
    session.add(reference); session.flush()
    vintage = ForecastVintage(company_id=company_id, execution_id=execution.execution_id, runtime_result_reference_id=reference.id, dataset_id=dataset_id, forecast_available_at=available_at, forecast_origin_period=cutoff, input_cutoff_period=cutoff, demand_type=demand_type, learning_score_at_run=learning, result_version='1.0.0', contract_version='1.0.0')
    session.add(vintage); session.flush()
    for index, (period, value) in enumerate(targets, 1):
        session.add(ForecastVintagePoint(forecast_vintage_id=vintage.id, material_code='SKU-1', target_period=period, forecast_value=Decimal(str(value)), lower_interval=Decimal(str(value - 1)), upper_interval=Decimal(str(value + 1)), model_used='model-'+label, selection_metadata={'fixture':label}, product_level='finished_good', product_group=product_group, product_class='class-'+label, horizon_index=index))
    session.flush()
    return vintage


def signature(rows):
    return [(row.target_period, str(row.forecast_vintage_id), str(row.forecast_vintage_point_id), str(row.forecast_value)) for row in rows]


def main():
    session = SessionLocal(); company = None; cid = uid = did = None
    prefix = 'phase3aa4_'+str(uuid7()).replace('-', '')
    try:
        company = Company(id=uuid7(), name=prefix, tax_id=prefix)
        user = User(id=uuid7(), company_id=company.id, email=prefix+'@x.invalid', hashed_password='x')
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id, dataset_hash=hashlib.sha256(prefix.encode()).hexdigest(), source_type=prefix, is_active=True)
        session.add_all((company, user, dataset)); session.flush()
        cid, uid, did = company.id, user.id, dataset.id
        a = add_vintage(session, cid, uid, did, 'A', iso_time('2026-W09'), '2026-W09', [(f'2026-W{week:02d}', 100+week) for week in range(10, 16)])
        b = add_vintage(session, cid, uid, did, 'B', iso_time('2026-W12'), '2026-W12', [(f'2026-W{week:02d}', 200+week) for week in range(13, 19)], product_group='snapshot-new', learning=Decimal('0.777'))
        c = add_vintage(session, cid, uid, did, 'C', iso_time('2026-W15', 1), '2026-W14', [('2026-W15', 315)], product_group='future')
        shipment = add_vintage(session, cid, uid, did, 'S', iso_time('2026-W12'), '2026-W12', [('2026-W13', 913)], demand_type='shipment', product_group='shipment')
        boundary = add_vintage(session, cid, uid, did, 'D', iso_time('2026-W40'), '2026-W39', [('2026-W40', 400)])
        year_end = add_vintage(session, cid, uid, did, 'Y', iso_time('2026-W52'), '2026-W52', [('2026-W53', 530)])
        add_vintage(session, cid, uid, did, 'invalid', iso_time('2026-W19'), '2026-W20', [('2026-W20', 999)])
        session.commit()

        service = EffectiveForecastTimelineService(session)
        rows = service.resolve(cid, 'sales', '2026-W10', '2026-W15', 'SKU-1')
        assert [row.target_period for row in rows] == [f'2026-W{week:02d}' for week in range(10, 16)]
        assert [row.forecast_vintage_id for row in rows] == [a.id, a.id, a.id, b.id, b.id, b.id]
        assert rows[-1].forecast_vintage_id == b.id and rows[-1].product_group == 'snapshot-new' and rows[-1].learning_score_at_run == Decimal('0.777')
        assert rows[0].learning_score_at_run is None and all(row.demand_type == 'sales' for row in rows)
        assert service.resolve(cid, 'shipment', '2026-W13', '2026-W13', 'SKU-1')[0].forecast_vintage_id == shipment.id
        assert service.resolve(cid, 'sales', '2026-W40', '2026-W40', 'SKU-1') == ()
        assert service.resolve(cid, 'sales', '2026-W53', '2026-W53', 'SKU-1')[0].forecast_vintage_id == year_end.id
        assert target_period_start('2026-W53') == datetime(2026, 12, 28, tzinfo=timezone.utc)
        try:
            service.resolve(cid, 'sales', '2026-W20', '2026-W20', 'SKU-1')
            raise AssertionError('malformed cutoff overlap was not rejected')
        except EffectiveForecastTimelineError:
            pass
        before = counts(session, cid); repeated = service.resolve(cid, 'sales', '2026-W10', '2026-W15', 'SKU-1'); session.commit()
        assert counts(session, cid) == before and signature(repeated) == signature(rows)
        expected = signature(rows); session.close(); session = SessionLocal()
        fresh = EffectiveForecastTimelineService(session).resolve(cid, 'sales', '2026-W10', '2026-W15', 'SKU-1')
        assert signature(fresh) == expected and counts(session, cid) == before
        print('PHASE3AA4 PASS', {'overlap':'B supersedes A for W13-W15', 'future_vintage':'C ineligible for W15', 'boundary':'W40 equality ineligible', 'year_boundary':'2026-W53', 'rows':len(fresh)}, flush=True)
    finally:
        if session:
            session.rollback()
        if company:
            ids = [value for value, in session.query(RuntimeExecution.execution_id).filter_by(company_id=cid)]
            vintage_ids = [value for value, in session.query(ForecastVintage.id).filter_by(company_id=cid)]
            session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).delete(synchronize_session=False)
            session.query(ForecastVintage).filter_by(company_id=cid).delete(synchronize_session=False)
            session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False)
            session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False)
            session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False)
            session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
            session.query(Dataset).filter_by(company_id=cid).delete(synchronize_session=False)
            session.query(User).filter_by(id=uid).delete(synchronize_session=False)
            session.query(Company).filter_by(id=cid).delete(synchronize_session=False)
            session.commit(); session.close()


if __name__ == '__main__':
    main()
