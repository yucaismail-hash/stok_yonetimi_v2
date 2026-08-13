"""Focused PostgreSQL proof for canonical Supplier Delivery Observation ledger."""
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.application.supplier_delivery_observations import SupplierDeliveryObservationError, SupplierDeliveryObservationService
from app.database import SessionLocal
from app.models.company import Company, MaterialSupplier, Supplier, User, UserMaterial
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution
from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision


def fixture(label):
    s = SessionLocal(); tag = 'supplier_observation_' + label + '_' + str(uuid7())
    try:
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + '@x.invalid', hashed_password='x')
        s.add_all((company, user)); s.flush()
        materials = {code: UserMaterial(id=uuid7(), user_id=user.id, company_id=company.id, material_code=code,
            material_name=code, product_level='raw_material') for code in ('X', 'Y')}
        suppliers = {code: Supplier(id=uuid7(), company_id=company.id, code=code, name=code) for code in ('A', 'B', 'C')}
        s.add_all((*materials.values(), *suppliers.values())); s.flush()
        # A serves X/Y, B serves X, and C only Y: all relevant scope shapes are explicit.
        s.add_all((MaterialSupplier(material_id=materials['X'].id, supplier_id=suppliers['A'].id, is_primary=True),
                   MaterialSupplier(material_id=materials['Y'].id, supplier_id=suppliers['A'].id),
                   MaterialSupplier(material_id=materials['X'].id, supplier_id=suppliers['B'].id),
                   MaterialSupplier(material_id=materials['Y'].id, supplier_id=suppliers['C'].id)))
        s.commit()
        return {'company_id': company.id, 'user_id': user.id, 'suppliers': {k: v.id for k, v in suppliers.items()},
                'materials': {k: v.id for k, v in materials.items()}}
    finally:
        s.close()


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
    finally:
        s.close()


def side_counts(company_id):
    s = SessionLocal()
    try:
        return (s.query(RuntimeExecution).filter_by(company_id=company_id).count(),
                s.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
                s.query(PatternLearningMemory).filter_by(company_id=company_id).count(),
                s.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).count(),
                s.query(RetrainingJob).filter_by(company_id=company_id).count(),
                s.query(LearningEvidence).filter_by(company_id=company_id).count(),
                s.query(LearningRefreshDelivery).filter_by(company_id=company_id).count())
    finally:
        s.close()


def create(service, root, supplier, material, receipt, *, dispatch=date(2026, 1, 1), promised=date(2026, 1, 8),
           ordered=100, received=100):
    return service.create(root['company_id'], root['suppliers'][supplier], material, source_system='erp',
        purchase_order_reference='PO-' + receipt.isoformat(), order_line_reference='LINE-1',
        receipt_reference='RCPT-' + receipt.isoformat(), dispatch_date=dispatch,
        promised_delivery_date=promised, actual_receipt_date=receipt, ordered_quantity=ordered,
        received_quantity=received, provenance={'source_record': receipt.isoformat()})


def main():
    roots = []
    try:
        root = fixture('a'); roots.append(root); other = fixture('b'); roots.append(other)
        service = SupplierDeliveryObservationService()
        assert side_counts(root['company_id']) == (0, 0, 0, 0, 0, 0, 0)
        # A/B: canonical observed event and exact source identity duplicate convergence.
        first = create(service, root, 'A', 'X', date(2026, 1, 9))
        same = create(service, root, 'A', 'X', date(2026, 1, 9))
        assert (first.status, same.status, first.observation_id, same.observation_id) == ('CREATED', 'ALREADY_EXISTS', first.observation_id, first.observation_id)
        current = service.get(root['company_id'], first.observation_id)
        assert current.observed_lead_time_days == 8 and current.delivery_lateness_days == 1 and current.on_time is False
        # C: genuine independent callers converge on one operational event.
        barrier = threading.Barrier(2)
        def concurrent():
            barrier.wait(); return create(SupplierDeliveryObservationService(), root, 'A', 'X', date(2026, 1, 10))
        with ThreadPoolExecutor(max_workers=2) as pool: outcomes = list(pool.map(lambda _: concurrent(), range(2)))
        assert sorted(row.status for row in outcomes) == ['ALREADY_EXISTS', 'CREATED']
        # D/E: supplier-material combinations are distinct ledger facts.
        b_x = create(service, root, 'B', 'X', date(2026, 1, 11))
        a_y = create(service, root, 'A', 'Y', date(2026, 1, 12))
        s = SessionLocal()
        try:
            scopes = {(row.supplier_id, row.material_code) for row in s.query(SupplierDeliveryObservation).filter_by(company_id=root['company_id'])}
            assert scopes == {(root['suppliers']['A'], 'X'), (root['suppliers']['B'], 'X'), (root['suppliers']['A'], 'Y')}
        finally: s.close()
        # G/H: accepted date then quantity corrections retain prior truth through immutable snapshots.
        date_revision = service.propose_correction(root['company_id'], first.observation_id, root['user_id'], actual_receipt_date=date(2026, 1, 7))
        assert date_revision.status == 'PROPOSED'
        accepted_date = service.accept_correction(root['company_id'], date_revision.revision_id, root['user_id'])
        after_date = service.get(root['company_id'], first.observation_id)
        assert accepted_date.status == 'ACCEPTED' and after_date.actual_receipt_date == date(2026, 1, 7) and after_date.observed_lead_time_days == 6 and after_date.on_time is True
        quantity_revision = service.propose_correction(root['company_id'], first.observation_id, root['user_id'], received_quantity=90)
        assert service.accept_correction(root['company_id'], quantity_revision.revision_id, root['user_id']).status == 'ACCEPTED'
        after_quantity = service.get(root['company_id'], first.observation_id)
        assert after_quantity.received_quantity == 90 and after_quantity.ordered_quantity == 100
        # I: rejected correction is auditable but leaves the canonical current truth untouched.
        rejected = service.propose_correction(root['company_id'], first.observation_id, root['user_id'], received_quantity=80)
        before_reject = (after_quantity.current_evidence_fingerprint, after_quantity.received_quantity)
        assert service.reject_correction(root['company_id'], rejected.revision_id, root['user_id']).status == 'REJECTED'
        after_reject = service.get(root['company_id'], first.observation_id)
        assert (after_reject.current_evidence_fingerprint, after_reject.received_quantity) == before_reject
        lineage = service.lineage(root['company_id'], first.observation_id)
        assert [row.approval_status for row in lineage] == ['accepted', 'accepted', 'rejected']
        assert lineage[0].previous_snapshot['actual_receipt_date'] == '2026-01-09' and lineage[1].previous_snapshot['received_quantity'] == '100.0000'
        # J/F: cross-tenant/mapping/date/quantity invalid source facts are rejected.
        invalid = (
            lambda: service.create(root['company_id'], other['suppliers']['A'], 'X', source_system='erp', receipt_reference='cross', actual_receipt_date=date(2026, 1, 1)),
            lambda: service.create(root['company_id'], root['suppliers']['C'], 'X', source_system='erp', receipt_reference='mismatch', actual_receipt_date=date(2026, 1, 1)),
            lambda: service.create(root['company_id'], root['suppliers']['A'], 'X', source_system='unknown', receipt_reference='source', actual_receipt_date=date(2026, 1, 1)),
            lambda: service.create(root['company_id'], root['suppliers']['A'], 'X', source_system='erp', receipt_reference='date', dispatch_date=date(2026, 1, 2), actual_receipt_date=date(2026, 1, 1)),
            lambda: service.create(root['company_id'], root['suppliers']['A'], 'X', source_system='erp', receipt_reference='quantity', actual_receipt_date=date(2026, 1, 1), ordered_quantity=0),
        )
        for action in invalid:
            try: action(); raise AssertionError('invalid supplier delivery was accepted')
            except SupplierDeliveryObservationError: pass
        assert service.get(other['company_id'], first.observation_id) is None
        try: service.propose_correction(other['company_id'], first.observation_id, other['user_id'], received_quantity=1); raise AssertionError('cross tenant correction succeeded')
        except LookupError: pass
        # K/M/N: fresh graph reconstructs the same truth, no master backfill and zero downstream activity.
        fresh = SupplierDeliveryObservationService().get(root['company_id'], first.observation_id)
        assert (fresh.supplier_id, fresh.material_code, fresh.actual_receipt_date, fresh.received_quantity,
                fresh.current_evidence_fingerprint) == (root['suppliers']['A'], 'X', date(2026, 1, 7), 90, after_reject.current_evidence_fingerprint)
        assert service.get(root['company_id'], b_x.observation_id).supplier_id == root['suppliers']['B']
        assert service.get(root['company_id'], a_y.observation_id).material_code == 'Y'
        assert side_counts(root['company_id']) == (0, 0, 0, 0, 0, 0, 0)
        print('PHASE 3C6B1 PROBE PASS', {'created': first.status, 'duplicate': same.status,
              'concurrent': [row.status for row in outcomes], 'accepted_date': accepted_date.status,
              'accepted_quantity': 'ACCEPTED', 'rejected': 'REJECTED', 'lineage': len(lineage)}, flush=True)
    finally:
        for root in reversed(roots): cleanup(root)


if __name__ == '__main__': main()
