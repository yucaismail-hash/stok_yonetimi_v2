"""PostgreSQL verification for read-only deterministic Supplier Learning."""
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.application.supplier_delivery_observations import SupplierDeliveryObservationService
from app.application.supplier_learning import SupplierLearningError, SupplierLearningService
from app.database import SessionLocal
from app.models.company import Company, MaterialSupplier, Supplier, User, UserMaterial
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.model_artifact import ModelArtifact
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution
from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision


def fixture(label):
    s = SessionLocal(); tag = 'supplier_learning_' + label + '_' + str(uuid7())
    try:
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + '@x.invalid', hashed_password='x')
        s.add_all((company, user)); s.flush()
        materials = {code: UserMaterial(id=uuid7(), user_id=user.id, company_id=company.id, material_code=code,
                     material_name=code, product_level='raw_material' if code == 'Y' else 'finished_good', group='G-' + code,
                     product_class='C-' + code) for code in ('X', 'Y')}
        suppliers = {code: Supplier(id=uuid7(), company_id=company.id, code=code, name='Supplier ' + code)
                     for code in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')}
        s.add_all((*materials.values(), *suppliers.values())); s.flush()
        s.add_all(MaterialSupplier(material_id=material.id, supplier_id=supplier.id)
                  for material in materials.values() for supplier in suppliers.values())
        s.commit()
        return {'company_id': company.id, 'user_id': user.id, 'materials': {k: v.id for k, v in materials.items()},
                'suppliers': {k: v.id for k, v in suppliers.items()}}
    finally: s.close()


def cleanup(root):
    s = SessionLocal()
    try:
        s.query(SupplierDeliveryObservationRevision).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(SupplierDeliveryObservation).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(MaterialSupplier).filter(MaterialSupplier.material_id.in_(tuple(root['materials'].values()))).delete(synchronize_session=False)
        s.query(UserMaterial).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(Supplier).filter_by(company_id=root['company_id']).delete(synchronize_session=False)
        s.query(User).filter_by(id=root['user_id']).delete(synchronize_session=False)
        s.query(Company).filter_by(id=root['company_id']).delete(synchronize_session=False); s.commit()
        assert s.query(Company).filter_by(id=root['company_id']).count() == 0
    finally: s.close()


def cleanup_interrupted_fixtures():
    """Recover only this probe's UUID-tagged fixtures after a DB disconnect."""
    s = SessionLocal()
    try:
        roots = [row.id for row in s.query(Company).filter(Company.name.like('supplier_learning_%')).all()]
        for company_id in roots:
            material_ids = [row.id for row in s.query(UserMaterial).filter_by(company_id=company_id).all()]
            s.query(SupplierDeliveryObservationRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
            s.query(SupplierDeliveryObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
            if material_ids:
                s.query(MaterialSupplier).filter(MaterialSupplier.material_id.in_(material_ids)).delete(synchronize_session=False)
            s.query(UserMaterial).filter_by(company_id=company_id).delete(synchronize_session=False)
            s.query(Supplier).filter_by(company_id=company_id).delete(synchronize_session=False)
            s.query(User).filter_by(company_id=company_id).delete(synchronize_session=False)
            s.query(Company).filter_by(id=company_id).delete(synchronize_session=False)
        s.commit()
        assert not s.query(Company).filter(Company.name.like('supplier_learning_%')).count()
    finally: s.close()


def side_counts(company_id):
    s = SessionLocal()
    try:
        return (s.query(SupplierDeliveryObservation).filter_by(company_id=company_id).count(),
                s.query(SupplierDeliveryObservationRevision).filter_by(company_id=company_id).count(),
                s.query(RuntimeExecution).filter_by(company_id=company_id).count(),
                s.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
                s.query(PatternLearningMemory).filter_by(company_id=company_id).count(),
                s.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).count(),
                s.query(RetrainingJob).filter_by(company_id=company_id).count(),
                s.query(LearningEvidence).filter_by(company_id=company_id).count(),
                s.query(LearningRefreshDelivery).filter_by(company_id=company_id).count(),
                s.query(ModelArtifact).filter_by(company_id=company_id).count())
    finally: s.close()


def add_series(root, supplier, material, leads, *, promised_mode='on_time', quantities=True, start=date(2026, 1, 1), prefix=''):
    # The production writer owns transaction boundaries.  Its usual per-call
    # short session is correct operationally, but repeatedly opening 100+ SSL
    # sessions destabilizes the shared development pool.  Preserve production
    # logic while keeping one genuine PostgreSQL session for this fixture batch.
    session = SessionLocal(); rows = []
    class FixtureSession:
        def __getattr__(self, name): return getattr(session, name)
        def close(self): pass
    try:
        writer = SupplierDeliveryObservationService(lambda: FixtureSession())
        for index, lead in enumerate(leads):
            # Keep dispatch spacing greater than the largest fixture lead time so
            # actual-receipt ordering represents the intended chronological series.
            dispatch = start + timedelta(days=index * 14)
            receipt = dispatch + timedelta(days=lead)
            if promised_mode == 'late': promised = receipt - timedelta(days=2)
            elif promised_mode == 'none': promised = None
            else: promised = receipt
            received = 70 if quantities == 'under' else 100 if quantities else None
            result = writer.create(root['company_id'], root['suppliers'][supplier], material, source_system='erp',
                purchase_order_reference=f'PO-{prefix}-{index}', order_line_reference='1', receipt_reference=f'RCPT-{prefix}-{index}',
                dispatch_date=dispatch, promised_delivery_date=promised, actual_receipt_date=receipt,
                ordered_quantity=100 if quantities else None, received_quantity=received,
                provenance={'fixture': prefix, 'index': index})
            rows.append(result.observation_id)
        return rows
    finally: session.close()


def calc(root, supplier, material, cutoff):
    s = SessionLocal()
    try: return SupplierLearningService(s).calculate(root['company_id'], root['suppliers'][supplier], material, cutoff)
    finally: s.close()


def scalar(result):
    return tuple(getattr(result, field) for field in result.__dataclass_fields__)


def main():
    roots = []
    try:
        cleanup_interrupted_fixtures()
        root = fixture('a'); roots.append(root); other = fixture('b'); roots.append(other)
        cutoff = date(2026, 6, 30)
        baseline_counts = side_counts(root['company_id'])
        # A-F/G: each policy class receives distinct canonical observed evidence.
        reliable_ids = add_series(root, 'A', 'X', [5] * 12, prefix='reliable')
        add_series(root, 'B', 'X', [2, 10] * 6, prefix='variable')
        add_series(root, 'C', 'X', [5] * 12, promised_mode='late', prefix='late')
        add_series(root, 'D', 'X', [5] * 12, quantities='under', prefix='fulfillment')
        add_series(root, 'E', 'X', [4] * 8 + [8] * 4, prefix='deteriorating')
        add_series(root, 'F', 'X', [2, 10] * 6, promised_mode='late', quantities='under', prefix='mixed')
        add_series(root, 'G', 'X', [5] * 3, prefix='insufficient')
        add_series(root, 'H', 'Y', [2, 10] * 6, prefix='multi-material')
        missing_promise = add_series(root, 'A', 'Y', [5] * 8, promised_mode='none', prefix='no-promise')
        missing_quantity = add_series(root, 'B', 'Y', [5] * 8, quantities=False, prefix='no-quantity')
        reliable = calc(root, 'A', 'X', cutoff); variable = calc(root, 'B', 'X', cutoff)
        late = calc(root, 'C', 'X', cutoff); fulfillment = calc(root, 'D', 'X', cutoff)
        deteriorating = calc(root, 'E', 'X', cutoff); mixed = calc(root, 'F', 'X', cutoff); insufficient = calc(root, 'G', 'X', cutoff)
        assert reliable.classification == 'RELIABLE' and reliable.sample_count == reliable.lead_time_sample_count == 12
        assert reliable.mean_observed_lead_time_days == reliable.median_observed_lead_time_days == 5.0 and reliable.std_observed_lead_time_days == 0.0
        assert reliable.p50_observed_lead_time_days == reliable.p90_observed_lead_time_days == 5.0 and reliable.on_time_ratio == 1.0
        assert variable.classification == 'VARIABLE' and variable.lead_time_coefficient_of_variation > .35
        assert late.classification == 'LATE_PRONE' and late.late_ratio == 1.0 and late.mean_lateness_days == 2.0
        assert fulfillment.classification == 'FULFILLMENT_RISK' and round(fulfillment.mean_fulfillment_ratio, 6) == .7 and fulfillment.underfulfillment_ratio == 1.0
        assert deteriorating.classification == 'DETERIORATING' and deteriorating.recent_deterioration_dimensions == ('LEAD_TIME_INCREASE',)
        assert mixed.classification == 'MIXED_RISK'
        assert insufficient.status == insufficient.classification == 'INSUFFICIENT_HISTORY' and insufficient.confidence == 0.0
        no_promise = calc(root, 'A', 'Y', cutoff); no_quantity = calc(root, 'B', 'Y', cutoff)
        assert no_promise.promised_delivery_sample_count == 0 and no_promise.on_time_ratio is None and no_promise.late_ratio is None
        assert no_quantity.fulfillment_sample_count == 0 and no_quantity.mean_fulfillment_ratio is None and no_quantity.underfulfillment_ratio is None
        # H/Q: post-cutoff canonical data cannot alter an earlier snapshot, even if it is poor evidence.
        before_future = calc(root, 'A', 'X', cutoff)
        add_series(root, 'A', 'X', [20, 20], promised_mode='late', quantities='under', start=date(2026, 7, 1), prefix='future')
        after_future = calc(root, 'A', 'X', cutoff)
        assert scalar(before_future) == scalar(after_future)
        # I/J/K: accepted corrections alter exactly their canonical dimensions; rejected correction is a no-op.
        writer = SupplierDeliveryObservationService()
        before_date = calc(root, 'A', 'X', cutoff)
        date_revision = writer.propose_correction(root['company_id'], reliable_ids[0], root['user_id'], actual_receipt_date=date(2026, 1, 4))
        assert writer.accept_correction(root['company_id'], date_revision.revision_id, root['user_id']).status == 'ACCEPTED'
        after_date = calc(root, 'A', 'X', cutoff)
        assert after_date.source_fingerprint != before_date.source_fingerprint and after_date.mean_observed_lead_time_days < before_date.mean_observed_lead_time_days
        before_quantity = after_date
        quantity_revision = writer.propose_correction(root['company_id'], reliable_ids[1], root['user_id'], received_quantity=80)
        assert writer.accept_correction(root['company_id'], quantity_revision.revision_id, root['user_id']).status == 'ACCEPTED'
        after_quantity = calc(root, 'A', 'X', cutoff)
        assert after_quantity.source_fingerprint != before_quantity.source_fingerprint and after_quantity.mean_fulfillment_ratio < before_quantity.mean_fulfillment_ratio
        rejected = writer.propose_correction(root['company_id'], reliable_ids[2], root['user_id'], received_quantity=50)
        assert writer.reject_correction(root['company_id'], rejected.revision_id, root['user_id']).status == 'REJECTED'
        after_rejected = calc(root, 'A', 'X', cutoff)
        assert scalar(after_quantity) == scalar(after_rejected)
        # N/O/P/R/S: source scope, tenant, determinism, fresh graph, and zero-mutating read boundary.
        assert reliable.source_observation_ids != variable.source_observation_ids and calc(root, 'A', 'Y', cutoff).material_code == 'Y'
        try: calc(other, 'A', 'X', cutoff) if False else SupplierLearningService(SessionLocal()).calculate(root['company_id'], other['suppliers']['A'], 'X', cutoff); raise AssertionError('cross tenant scope was accepted')
        except SupplierLearningError: pass
        again = calc(root, 'A', 'X', cutoff)
        fresh = calc(root, 'A', 'X', cutoff)
        assert scalar(again) == scalar(fresh) and fresh.source_fingerprint == after_rejected.source_fingerprint
        after_counts = side_counts(root['company_id'])
        assert after_counts[:2] == (baseline_counts[0] + 105, baseline_counts[1] + 3)
        assert after_counts[2:] == baseline_counts[2:]
        empty = calc(other, 'A', 'X', cutoff)
        assert empty.status == 'ABSENT' and empty.classification == 'INSUFFICIENT_HISTORY'
        print('PHASE 3C6B2 PROBE PASS', {'reliable': reliable.classification, 'variable': variable.classification,
              'late': late.classification, 'fulfillment': fulfillment.classification, 'deteriorating': deteriorating.classification,
              'mixed': mixed.classification, 'insufficient': insufficient.status, 'source_observations': after_counts[0]}, flush=True)
    finally:
        for root in reversed(roots): cleanup(root)


if __name__ == '__main__': main()
