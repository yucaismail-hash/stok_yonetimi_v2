"""PostgreSQL probe for canonical actual weekly observations and revision ledger."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7
from app.application.actual_weekly_ledger import ActualWeeklyLedgerError, ActualWeeklyLedgerService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


def fixture(tag):
    session = SessionLocal(); probe = "phase3aa2_" + tag + "_" + str(uuid7()).replace("-", "")
    try:
        company = Company(id=uuid7(), name=probe, tax_id=probe); user = User(id=uuid7(), company_id=company.id, email=probe + "@example.invalid", hashed_password="probe")
        session.add_all((company, user)); session.flush()
        payload = {"items": [{"sku_code": "SOURCE", "demand_history": [1, 2, 3, 4]}]}
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id, dataset_hash=hashlib.sha256((probe + json.dumps(payload)).encode()).hexdigest(), source_type=probe, encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True)
        session.add(dataset); session.commit(); return probe, company.id, user.id, dataset.id
    finally: session.close()


def cleanup(item):
    probe, company_id, user_id, _ = item; session = SessionLocal()
    try:
        session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(Dataset).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(CompanyEncryptionKey).filter_by(user_id=user_id).delete(synchronize_session=False)
        session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
        session.query(Company).filter_by(id=company_id).delete(synchronize_session=False); session.commit()
    finally: session.close()


def rows(start, end, level="Mamul", code="SKU-A", quantity=100):
    return [{"material_code": code, "period": f"2026-W{week:02d}", "quantity": quantity, "product_level": level, "product_group": "Group-1", "product_class": "Class-1"} for week in range(start, end + 1)]


def main():
    primary = tenant = None
    try:
        primary = fixture("primary"); tenant = fixture("tenant")
        service = ActualWeeklyLedgerService(); base = rows(1, 10)
        first = service.ingest_dataset_actuals(primary[1], primary[2], primary[3], base, "sales"); assert first["new"] == 10
        repeat = service.ingest_dataset_actuals(primary[1], primary[2], primary[3], base, "sales"); assert repeat["new"] == 0 and repeat["noop"] == 10
        partial = service.ingest_dataset_actuals(primary[1], primary[2], primary[3], rows(1, 13), "sales"); assert partial["new"] == 3 and partial["noop"] == 10
        correction = rows(8, 8, quantity=180); proposed = service.ingest_dataset_actuals(primary[1], primary[2], primary[3], correction, "sales"); assert proposed["proposed"] == 1
        session = SessionLocal(); observation = session.query(ActualWeeklyObservation).filter_by(company_id=primary[1], material_code="SKU-A", period="2026-W08", demand_type="sales").one(); assert float(observation.quantity) == 100; revision = session.query(ActualWeeklyRevision).filter_by(company_id=primary[1], observation_id=observation.id, approval_status="proposed").one(); correction_id = revision.id; session.close()
        service.approve_revision(primary[1], correction_id, primary[2])
        rejected = service.ingest_dataset_actuals(primary[1], primary[2], primary[3], rows(9, 9, quantity=190), "sales"); assert rejected["proposed"] == 1
        session = SessionLocal(); rejected_revision = session.query(ActualWeeklyRevision).filter_by(company_id=primary[1], material_code="SKU-A", period="2026-W09", approval_status="proposed").one(); rejected_id = rejected_revision.id; session.close(); service.reject_revision(primary[1], rejected_id, primary[2])
        # Product levels and same-SKU demand-type coexistence are distinct current identities.
        service.ingest_dataset_actuals(primary[1], primary[2], primary[3], rows(1, 1, level="Yarı Mamul", code="SKU-B", quantity=40), "sales")
        service.ingest_dataset_actuals(primary[1], primary[2], primary[3], rows(1, 1, level="Hammadde", code="SKU-C", quantity=30), "sales")
        service.ingest_dataset_actuals(primary[1], primary[2], primary[3], rows(1, 1, code="SKU-A", quantity=55), "consumption")
        session = SessionLocal(); observations = session.query(ActualWeeklyObservation).filter_by(company_id=primary[1]).all(); revisions = session.query(ActualWeeklyRevision).filter_by(company_id=primary[1]).all()
        lookup = {(row.material_code, row.period, row.demand_type): row for row in observations}
        assert len(lookup) == 16 and float(lookup[("SKU-A", "2026-W08", "sales")].quantity) == 180 and float(lookup[("SKU-A", "2026-W09", "sales")].quantity) == 100 and float(lookup[("SKU-A", "2026-W01", "consumption")].quantity) == 55
        assert {lookup[("SKU-A", "2026-W01", "sales")].product_level, lookup[("SKU-B", "2026-W01", "sales")].product_level, lookup[("SKU-C", "2026-W01", "sales")].product_level} == {"finished_good", "semi_finished_good", "raw_material"}
        assert any(row.change_type == "correction" and row.approval_status == "accepted" and float(row.previous_quantity) == 100 and float(row.proposed_quantity) == 180 for row in revisions)
        assert any(row.change_type == "correction" and row.approval_status == "rejected" for row in revisions); session.close()
        try: service.ingest_dataset_actuals(tenant[1], tenant[2], primary[3], base, "sales"); raise AssertionError("tenant dataset access accepted")
        except ActualWeeklyLedgerError: pass
        # Fresh session reconstruction relies only on persisted company identity.
        session = SessionLocal(); assert session.query(ActualWeeklyObservation).filter_by(company_id=primary[1]).count() == 16 and session.query(ActualWeeklyRevision).filter_by(company_id=primary[1]).count() == 18; session.close()
        print("PHASE3AA2 PASS", json.dumps({"observations": 16, "revisions": 18, "identity": "company/material_code/period/demand_type", "approved_correction": "100->180", "rejected_correction_preserved": True}), flush=True)
    finally:
        if primary: cleanup(primary)
        if tenant: cleanup(tenant)


if __name__ == "__main__": main()
