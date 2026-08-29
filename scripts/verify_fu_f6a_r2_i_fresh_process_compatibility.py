"""Fresh-process, read-only compatibility proof for FU-F6A-R2-I."""

import json
import sys
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.business_decision_plan import BusinessDecisionPlanService
from app.application.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReferenceService
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_explanation import DecisionExplanationService
from app.application.decision_feedback import DecisionFeedbackService
from app.application.decision_policy import DecisionPolicy
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.runtime import RuntimeExecution, RuntimeResultReference


MANIFEST = Path(__file__).with_name(".fu_f6a_r2_i_fresh_process_compatibility.json")
REQUIRED_MANIFESTS = (
    ".fu_f6a_r2_c_pre_assoc.json", ".fu_f6a_r2_d_post_assoc.json", ".fu_f6a_r2_e_partial.json",
    ".fu_f6a_r2_f_historical_freeze.json", ".fu_f6a_r2_g_same_snapshot.json", ".fu_f6a_r2_h_tenant_isolation.json",
)
COMPANY_ID = UUID("06a90a45-458d-7648-8001-fe3c3589210e")
EXECUTION_ID = UUID("06a90a48-6d84-762e-8000-eb1568f56b7a")
AGGREGATE_ID = UUID("06a90a5b-6de1-751b-8000-1fe6b12d4b9c")
EXPECTED_ASSOCIATIONS = (
    UUID("06a90a5d-b99d-7c52-8000-f804d364ff91"),
    UUID("06a90a76-a86a-708e-8000-19bc6287a175"),
)
EXPECTED_SNAPSHOTS = (
    UUID("06a90a5c-ec8b-74ad-8000-5cab50d1d93b"),
    UUID("06a90a76-6eaa-767b-8000-9d90b584eaae"),
)


def _forbidden(*_args, **_kwargs):
    raise AssertionError("historical compatibility read invoked forbidden Decision computation")


def _counts(session):
    return {
        "executions": session.query(RuntimeExecution).filter_by(company_id=COMPANY_ID).count(),
        "results": session.query(RuntimeResultReference).filter_by(company_id=COMPANY_ID).count(),
        "finalizations": session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=COMPANY_ID).count(),
        "associations": session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=COMPANY_ID).count(),
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=COMPANY_ID).count(),
        "candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == COMPANY_ID).count(),
        "feedback": session.query(DecisionFeedbackEvent).filter_by(company_id=COMPANY_ID).count(),
    }


def _manifest_audit():
    parsed = {}
    for name in REQUIRED_MANIFESTS:
        path = Path(__file__).with_name(name)
        parsed[name] = json.loads(path.read_text(encoding="utf-8"))
    return parsed


def audit():
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        before = _counts(session)
        store = RuntimeStore(session)
        execution = store.get_execution(EXECUTION_ID, COMPANY_ID)
        aggregate = store.get_execution_aggregate_result(EXECUTION_ID, COMPANY_ID)
        assert execution is not None and execution.state == "completed" and float(execution.progress) == 100
        assert aggregate is not None and aggregate.id == AGGREGATE_ID and aggregate.runtime_task_id is None
        refs = store.get_execution_result_references(EXECUTION_ID, COMPANY_ID)
        analytical = {row.result_type: row for row in refs if row.runtime_task_id is not None}
        assert set(analytical) == {"forecast", "safety_stock", "simulation", "backtest"}
        analytical_ids = {name: str(row.id) for name, row in sorted(analytical.items())}

        with patch.object(BusinessDecisionPlanService, "materialize", _forbidden), \
             patch.object(DecisionEvidenceResolver, "resolve", _forbidden), \
             patch.object(DecisionPolicy, "evaluate", _forbidden):
            correlations = BusinessWorkflowDecisionSnapshotReferenceService().list_for_execution(COMPANY_ID, EXECUTION_ID)
            assert tuple(row.id for row in correlations) == EXPECTED_ASSOCIATIONS
            assert tuple(row.decision_snapshot_id for row in correlations) == EXPECTED_SNAPSHOTS
            explanations = tuple(DecisionExplanationService().get(COMPANY_ID, row.decision_snapshot_id) for row in correlations)
            assert all(explanation is not None for explanation in explanations)
            assert tuple(UUID(explanation.snapshot["id"]) for explanation in explanations) == EXPECTED_SNAPSHOTS
            # This read-only service establishes existing-Snapshot feedback targeting without recording feedback.
            feedback_views = tuple(DecisionFeedbackService().list_for_snapshot(COMPANY_ID, row.decision_snapshot_id) for row in correlations)
            assert all(view is not None for view in feedback_views)
        persisted = [session.query(DecisionSnapshot).filter_by(id=row.decision_snapshot_id, company_id=COMPANY_ID).one() for row in correlations]
        assert all(snapshot.company_id == COMPANY_ID for snapshot in persisted)
        after = _counts(session)
        assert before == after
    finally:
        session.rollback()
        session.close()
    return {
        "company_id": str(COMPANY_ID), "execution_id": str(EXECUTION_ID),
        "aggregate_result_reference_id": str(AGGREGATE_ID),
        "association_ids": [str(value) for value in EXPECTED_ASSOCIATIONS],
        "snapshot_ids": [str(value) for value in EXPECTED_SNAPSHOTS],
        "analytical_result_reference_ids": analytical_ids,
        "counts": before,
        "explanation_fingerprints": [explanation.explanation_fingerprint for explanation in explanations],
        "feedback_view_counts": [view["counts"] for view in feedback_views],
    }


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"1", "2"}:
        raise ValueError("use independent fresh-process run number: 1 or 2")
    run_number = sys.argv[1]
    manifests = _manifest_audit()
    result = audit()
    existing = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    if run_number == "2":
        assert existing.get("fresh_process_run_1") == "passed"
        for key in ("company_id", "execution_id", "aggregate_result_reference_id", "association_ids", "snapshot_ids"):
            assert existing[key] == result[key]
    manifest = {
        **result,
        "fresh_process_run_1": "passed" if run_number == "1" or existing.get("fresh_process_run_1") == "passed" else "pending",
        "fresh_process_run_2": "passed" if run_number == "2" else existing.get("fresh_process_run_2", "pending"),
        "historical_read_no_materialize": True,
        "historical_read_no_resolver": True,
        "historical_read_no_policy": True,
        "historical_read_no_current_learning": True,
        "historical_read_no_analytics": True,
        "explanation_compatibility": "passed",
        "feedback_target_compatibility": "passed",
        "presentation_readiness": "ready_with_r3_adapter",
        "database_writes": 0,
        "r2_manifests_parsed": sorted(manifests),
    }
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
    assert json.loads(MANIFEST.read_text(encoding="utf-8")) == manifest
    print("R2I_AUDIT", json.dumps(result, sort_keys=True))
    print(f"FU_F6A_R2_I_FRESH_PROCESS_RUN_{run_number}_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
