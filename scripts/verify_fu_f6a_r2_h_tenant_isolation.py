"""Read-only fresh-process tenant-isolation proof for FU-F6A-R2-H."""

import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReferenceService
from app.application.decision_snapshot import DecisionSnapshotService
from app.database import SessionLocal
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate


MANIFEST = Path(__file__).with_name(".fu_f6a_r2_h_tenant_isolation.json")
COMPANY_A = UUID("06a90a45-458d-7648-8001-fe3c3589210e")
EXECUTION_A = UUID("06a90a48-6d84-762e-8000-eb1568f56b7a")
FINALIZATION_A = UUID("06a90a5b-c345-7b04-8000-adb9b516f9da")
COMPANY_B = UUID("06a8f44a-18e1-7a2e-8001-12f83fc644df")
EXECUTION_B = UUID("06a8f44b-eefc-7229-8000-e409b55b503a")
FINALIZATION_B = UUID("06a8f456-0423-7555-8000-4f664b236c8d")


def counts(session, company_id):
    return {
        "associations": session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=company_id).count(),
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=company_id).count(),
        "candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count(),
    }


def association_view(rows):
    return [{"association_id": str(row.id), "snapshot_id": str(row.decision_snapshot_id), "finalization_id": str(row.decision_finalization_id), "material_code": row.material_code} for row in rows]


def main():
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        before = {"company_a": counts(session, COMPANY_A), "company_b": counts(session, COMPANY_B)}
        # The canonical correlation boundary owns both company and execution predicates.
        service = BusinessWorkflowDecisionSnapshotReferenceService()
        a_rows = service.list_for_execution(COMPANY_A, EXECUTION_A)
        b_rows = service.list_for_execution(COMPANY_B, EXECUTION_B)
        a_reads_b = service.list_for_execution(COMPANY_A, EXECUTION_B)
        b_reads_a = service.list_for_execution(COMPANY_B, EXECUTION_A)
        assert len(a_rows) == 2 and len(b_rows) == 1
        assert not a_reads_b and not b_reads_a
        assert {str(row.id) for row in a_rows} == {
            "06a90a5d-b99d-7c52-8000-f804d364ff91", "06a90a76-a86a-708e-8000-19bc6287a175"
        }
        assert {str(row.decision_snapshot_id) for row in a_rows} == {
            "06a90a5c-ec8b-74ad-8000-5cab50d1d93b", "06a90a76-6eaa-767b-8000-9d90b584eaae"
        }
        # DecisionSnapshotService.get is the production company-scoped Snapshot lookup.
        snapshot_service = DecisionSnapshotService()
        assert snapshot_service.get(COMPANY_A, b_rows[0].decision_snapshot_id) is None
        assert snapshot_service.get(COMPANY_B, a_rows[0].decision_snapshot_id) is None
        assert session.query(BusinessWorkflowDecisionFinalization).filter_by(
            id=FINALIZATION_B, company_id=COMPANY_A, execution_id=EXECUTION_B
        ).one_or_none() is None
        assert session.query(BusinessWorkflowDecisionFinalization).filter_by(
            id=FINALIZATION_A, company_id=COMPANY_B, execution_id=EXECUTION_A
        ).one_or_none() is None
        constraints = [
            dict(row)
            for row in session.execute(text("""
                SELECT conname AS name, pg_get_constraintdef(oid, true) AS definition
                FROM pg_constraint
                WHERE conrelid = to_regclass('public.business_workflow_decision_snapshot_references')
                  AND contype = 'f'
                ORDER BY conname
            """)).mappings()
        ]
        names = {row["name"] for row in constraints}
        assert {"fk_bw_dsref_execution_company", "fk_bw_dsref_finalization_execution_company", "fk_bw_dsref_snapshot_company"} <= names
        after = {"company_a": counts(session, COMPANY_A), "company_b": counts(session, COMPANY_B)}
        assert before == after
    finally:
        session.rollback()
        session.close()

    manifest = {
        "company_a_id": str(COMPANY_A), "execution_a_id": str(EXECUTION_A),
        "association_a_ids": [item["association_id"] for item in association_view(a_rows)],
        "snapshot_a_ids": [item["snapshot_id"] for item in association_view(a_rows)],
        "company_b_id": str(COMPANY_B), "execution_b_id": str(EXECUTION_B),
        "association_b_ids": [item["association_id"] for item in association_view(b_rows)],
        "snapshot_b_ids": [item["snapshot_id"] for item in association_view(b_rows)],
        "a_reads_a": True, "b_reads_b": True,
        "a_reads_b_foreign_count": len(a_reads_b), "b_reads_a_foreign_count": len(b_reads_a),
        "snapshot_cross_tenant_lookup_blocked": True,
        "finalization_ownership_verified": True,
        "db_composite_ownership_verified": True,
        "database_writes": 0,
    }
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
    assert json.loads(MANIFEST.read_text(encoding="utf-8")) == manifest
    print("R2H_POSITIVE_A", association_view(a_rows))
    print("R2H_POSITIVE_B", association_view(b_rows))
    print("R2H_COUNTS", before)
    print("R2H_FOREIGN_COUNTS", {"a_reads_b": len(a_reads_b), "b_reads_a": len(b_reads_a)})
    print("R2H_FK_CONSTRAINTS", constraints)
    print("FU_F6A_R2_H_TENANT_ISOLATION_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
