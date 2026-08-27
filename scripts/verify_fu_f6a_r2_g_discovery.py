"""Read-only R2-G discovery: Snapshot semantic identity and retained-fixture topology."""

import sys
from pathlib import Path
from uuid import UUID
from hashlib import sha256
from json import dumps

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.application.decision_evidence_resolver import DecisionEvidenceEnvelope
from app.application.decision_policy import DecisionPolicy


FIXTURE_COMPANIES = (
    UUID("06a8f44a-18e1-7a2e-8001-12f83fc644df"),
    UUID("06a90a45-458d-7648-8001-fe3c3589210e"),
)


def constraints(session, table):
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT conname AS name, contype AS kind, pg_get_constraintdef(oid, true) AS definition
                FROM pg_constraint
                WHERE conrelid = to_regclass(:table_name)
                ORDER BY conname
                """
            ),
            {"table_name": f"public.{table}"},
        ).mappings()
    ]


def main():
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        association_constraints = constraints(session, "business_workflow_decision_snapshot_references")
        snapshot_constraints = constraints(session, "decision_snapshots")
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT r.company_id::text, r.execution_id::text, r.id::text AS association_id,
                           r.decision_finalization_id::text, r.decision_snapshot_id::text,
                           r.material_code, r.demand_type, r.decision_context, r.decision_cutoff_period,
                           s.decision_evidence_fingerprint, s.decision_policy_fingerprint,
                           s.decision_policy_version
                    FROM business_workflow_decision_snapshot_references r
                    JOIN decision_snapshots s ON s.id = r.decision_snapshot_id AND s.company_id = r.company_id
                    WHERE r.company_id = ANY(:company_ids)
                    ORDER BY r.company_id, r.execution_id, r.material_code
                    """
                ),
                {"company_ids": list(FIXTURE_COMPANIES)},
            ).mappings()
        ]
        shared = {}
        for row in rows:
            shared.setdefault(row["decision_snapshot_id"], set()).add(row["execution_id"])
        shared = {snapshot: sorted(executions) for snapshot, executions in shared.items() if len(executions) > 1}
        assert not shared, "a retained R2 shared-Snapshot pair was expected to be reported, not treated as failure"
        source_provenance = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT id::text AS snapshot_id, source_provenance
                    FROM decision_snapshots
                    WHERE id IN (
                        '06a90a5c-ec8b-74ad-8000-5cab50d1d93b'::uuid,
                        '06a90a76-6eaa-767b-8000-9d90b584eaae'::uuid
                    )
                    ORDER BY id
                    """
                )
            ).mappings()
        ]
        required_a = (
            ("forecast", {"status": "AVAILABLE", "source_id": "runtime-result-a", "runtime_result_reference_id": "runtime-result-a", "cutoff_period": "2026-W32", "versions": ("1", "1")}),
            ("safety_stock", {"status": "AVAILABLE", "source_id": "runtime-result-a", "runtime_result_reference_id": "runtime-result-a", "cutoff_period": "2026-W32", "result_version": "1", "contract_version": "1"}),
        )
        required_b = tuple(
            (name, {key: ("runtime-result-b" if key in {"source_id", "runtime_result_reference_id"} else value) for key, value in row.items()})
            for name, row in required_a
        )
        def envelope(required):
            semantic = {
                "company_id": "company-a", "material_code": "SKU-A", "demand_type": "sales",
                "cutoff": "2026-W32", "context": "REPLENISHMENT", "required": required, "optional": (),
            }
            fingerprint = sha256(dumps(semantic, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
            return DecisionEvidenceEnvelope("company-a", "SKU-A", "sales", "2026-W32", "REPLENISHMENT", "READY", required, (), (), fingerprint)
        envelope_a, envelope_b = envelope(required_a), envelope(required_b)
        policy_a, policy_b = DecisionPolicy().evaluate(envelope_a), DecisionPolicy().evaluate(envelope_b)
        assert envelope_a.fingerprint != envelope_b.fingerprint
        assert policy_a.fingerprint != policy_b.fingerprint
        assert policy_a.candidates == policy_b.candidates
        print("R2G_ASSOCIATION_CONSTRAINTS", association_constraints)
        print("R2G_SNAPSHOT_CONSTRAINTS", snapshot_constraints)
        print("R2G_RETAINED_ASSOCIATIONS", rows)
        print("R2G_RETAINED_SHARED_SNAPSHOTS", shared)
        print("R2G_SOURCE_PROVENANCE", source_provenance)
        print("R2G_CONTROLLED_UUID_COMPARISON", {
            "only_changed_fields": ("required[*].source_id", "required[*].runtime_result_reference_id"),
            "evidence_fingerprint_a": envelope_a.fingerprint,
            "evidence_fingerprint_b": envelope_b.fingerprint,
            "policy_fingerprint_a": policy_a.fingerprint,
            "policy_fingerprint_b": policy_b.fingerprint,
            "policy_content_equal": policy_a.candidates == policy_b.candidates,
        })
        print("R2G_DISCOVERY_COMPLETE")
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    main()
