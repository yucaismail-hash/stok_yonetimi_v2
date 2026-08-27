"""Read-only live PostgreSQL catalog and historical-correlation audit for FU-F6A-R2-F."""

import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.business_workflow_decision_snapshot_reference import (
    BusinessWorkflowDecisionSnapshotReferenceService,
)
from app.database import SessionLocal
from app.models.business_workflow_decision_finalization import (
    BusinessWorkflowDecisionFinalization,
)
from app.models.business_workflow_decision_snapshot_reference import (
    BusinessWorkflowDecisionSnapshotReference,
)
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.runtime import RuntimeExecution, RuntimeResultReference


MANIFEST = Path(__file__).with_name(".fu_f6a_r2_f_historical_freeze.json")
ASSOCIATION_TABLE = "business_workflow_decision_snapshot_references"
SNAPSHOT_TABLE = "decision_snapshots"
CANDIDATE_TABLE = "decision_snapshot_candidates"


def _catalog_table(session, table_name):
    row = session.execute(
        text(
            """
            SELECT n.nspname AS schema_name, c.relname AS table_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.oid = to_regclass(:qualified_name)
            """
        ),
        {"qualified_name": f"public.{table_name}"},
    ).mappings().one_or_none()
    assert row is not None, f"live table missing: {table_name}"
    return dict(row)


def _constraints(session, table_name):
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT c.conname AS name, c.contype AS kind,
                       pg_get_constraintdef(c.oid, true) AS definition
                FROM pg_constraint c
                WHERE c.conrelid = to_regclass(:qualified_name)
                ORDER BY c.conname
                """
            ),
            {"qualified_name": f"public.{table_name}"},
        ).mappings()
    ]


def _indexes(session, table_name):
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT i.relname AS name, pg_get_indexdef(i.oid) AS definition
                FROM pg_index x
                JOIN pg_class i ON i.oid = x.indexrelid
                WHERE x.indrelid = to_regclass(:qualified_name)
                ORDER BY i.relname
                """
            ),
            {"qualified_name": f"public.{table_name}"},
        ).mappings()
    ]


def _triggers(session, table_name):
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT t.tgname AS trigger_name,
                       t.tgenabled AS enabled_state,
                       pg_get_triggerdef(t.oid, true) AS definition,
                       pn.nspname AS function_schema,
                       p.proname AS function_name,
                       pg_get_functiondef(p.oid) AS function_definition
                FROM pg_trigger t
                JOIN pg_proc p ON p.oid = t.tgfoid
                JOIN pg_namespace pn ON pn.oid = p.pronamespace
                WHERE t.tgrelid = to_regclass(:qualified_name)
                  AND NOT t.tgisinternal
                ORDER BY t.tgname
                """
            ),
            {"qualified_name": f"public.{table_name}"},
        ).mappings()
    ]


def _catalog(session):
    association = _catalog_table(session, ASSOCIATION_TABLE)
    constraints = _constraints(session, ASSOCIATION_TABLE)
    indexes = _indexes(session, ASSOCIATION_TABLE)
    triggers = _triggers(session, ASSOCIATION_TABLE)
    immutable = next(
        (row for row in triggers if row["trigger_name"] == "trg_business_workflow_decision_snapshot_reference_immutable"),
        None,
    )
    assert immutable is not None and immutable["enabled_state"] == "O", "association immutability trigger is absent or disabled"
    assert "BEFORE UPDATE" in immutable["definition"] and "business_workflow_decision_snapshot_reference_reject_update" in immutable["definition"]
    assert "RAISE EXCEPTION" in immutable["function_definition"]

    expected_fks = {
        "fk_bw_dsref_execution_company",
        "fk_bw_dsref_finalization_execution_company",
        "fk_bw_dsref_snapshot_company",
    }
    fk_names = {row["name"] for row in constraints if row["kind"] == "f"}
    assert expected_fks <= fk_names, f"missing ownership FKs: {expected_fks - fk_names}"
    assert any(row["name"] == "uq_business_decision_snapshot_reference_execution_scope" for row in constraints)

    snapshot_triggers = _triggers(session, SNAPSHOT_TABLE)
    candidate_triggers = _triggers(session, CANDIDATE_TABLE)
    snapshot_immutable = next((row for row in snapshot_triggers if row["trigger_name"] == "trg_decision_snapshots_immutable"), None)
    candidate_immutable = next((row for row in candidate_triggers if row["trigger_name"] == "trg_decision_snapshot_candidates_immutable"), None)
    assert snapshot_immutable is not None and snapshot_immutable["enabled_state"] == "O"
    assert candidate_immutable is not None and candidate_immutable["enabled_state"] == "O"
    for trigger in (snapshot_immutable, candidate_immutable):
        assert "BEFORE UPDATE" in trigger["definition"]
        assert "RAISE EXCEPTION" in trigger["function_definition"]

    return {
        "association": association,
        "constraints": constraints,
        "indexes": indexes,
        "immutable_trigger": immutable,
        "snapshot_immutable": snapshot_immutable,
        "candidate_immutable": candidate_immutable,
    }


def _validate_and_read(session, manifest):
    company_id = UUID(manifest["company_id"])
    execution_id = UUID(manifest["execution_id"])
    finalization_id = UUID(manifest["finalization_id"])
    aggregate_id = UUID(manifest["aggregate_result_id"])

    execution = session.query(RuntimeExecution).filter_by(execution_id=execution_id, company_id=company_id).one()
    assert execution.state == "completed"
    aggregate = session.query(RuntimeResultReference).filter_by(
        id=aggregate_id, company_id=company_id, execution_id=execution_id, result_type="business_workflow"
    ).one()
    assert aggregate.runtime_task_id is None
    finalization = session.query(BusinessWorkflowDecisionFinalization).filter_by(
        id=finalization_id, company_id=company_id, execution_id=execution_id
    ).one()
    assert finalization.status == "succeeded" and finalization.attempt_count == manifest["finalization_attempt_count"]

    before = {
        "associations": session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=company_id, execution_id=execution_id).count(),
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=company_id).count(),
        "candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count(),
    }
    expected = {entry["material_code"]: entry for entry in (manifest["sku_a"], manifest["sku_b"])}
    rows = BusinessWorkflowDecisionSnapshotReferenceService().list_for_execution(company_id, execution_id)
    assert len(rows) == 2
    assert {row.material_code for row in rows} == set(expected)
    candidate_ids = {}
    for row in rows:
        entry = expected[row.material_code]
        assert str(row.id) == entry["association_id"]
        assert str(row.decision_snapshot_id) == entry["snapshot_id"]
        assert row.decision_finalization_id == finalization.id
        snapshot = session.query(DecisionSnapshot).filter_by(id=row.decision_snapshot_id, company_id=company_id).one()
        assert (row.material_code, row.demand_type, row.decision_context, row.decision_cutoff_period) == (
            snapshot.material_code, snapshot.demand_type, snapshot.decision_context, snapshot.decision_cutoff_period
        )
        candidate_ids[row.material_code] = [
            str(candidate.id) for candidate in session.query(DecisionSnapshotCandidate).filter_by(
                decision_snapshot_id=snapshot.id
            ).order_by(DecisionSnapshotCandidate.ordinal, DecisionSnapshotCandidate.id)
        ]
    after = {
        "associations": session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=company_id, execution_id=execution_id).count(),
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=company_id).count(),
        "candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count(),
    }
    assert before == after == {
        "associations": manifest["baseline_association_count"],
        "snapshots": manifest["baseline_snapshot_count"],
        "candidates": manifest["baseline_candidate_count"],
    }
    return before, candidate_ids


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    session = SessionLocal()
    try:
        # This is intentionally the first statement: every database action in this probe is SELECT-only.
        session.execute(text("SET TRANSACTION READ ONLY"))
        catalog = _catalog(session)
        counts, candidate_ids = _validate_and_read(session, manifest)
    finally:
        session.rollback()
        session.close()

    manifest["sku_a"]["candidate_ids"] = candidate_ids[manifest["sku_a"]["material_code"]]
    manifest["sku_b"]["candidate_ids"] = candidate_ids[manifest["sku_b"]["material_code"]]
    manifest.update({
        "catalog_immutability_audit": "passed",
        "association_table": f"{catalog['association']['schema_name']}.{catalog['association']['table_name']}",
        "trigger_name": catalog["immutable_trigger"]["trigger_name"],
        "trigger_enabled": catalog["immutable_trigger"]["enabled_state"],
        "trigger_definition": catalog["immutable_trigger"]["definition"],
        "trigger_function": f"{catalog['immutable_trigger']['function_schema']}.{catalog['immutable_trigger']['function_name']}",
        "ownership_constraint_names": [row["name"] for row in catalog["constraints"]],
        "snapshot_immutability_level": "DB-enforced immutable",
        "candidate_immutability_level": "DB-enforced immutable",
        "final_read_verified": True,
        "database_writes": 0,
    })
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
    reopened = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert reopened["catalog_immutability_audit"] == "passed" and reopened["database_writes"] == 0
    print("CATALOG_ASSOCIATION", json.dumps(catalog["association"], sort_keys=True))
    print("CATALOG_CONSTRAINTS", json.dumps(catalog["constraints"], sort_keys=True))
    print("CATALOG_INDEXES", json.dumps(catalog["indexes"], sort_keys=True))
    print("CATALOG_ASSOCIATION_TRIGGER", json.dumps(catalog["immutable_trigger"], sort_keys=True))
    print("CATALOG_SNAPSHOT_TRIGGER", json.dumps(catalog["snapshot_immutable"], sort_keys=True))
    print("CATALOG_CANDIDATE_TRIGGER", json.dumps(catalog["candidate_immutable"], sort_keys=True))
    print("FINAL_READ_COUNTS", json.dumps(counts, sort_keys=True))
    print("FU_F6A_R2_F_HISTORICAL_FREEZE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
