"""Focused retained-fixture verification for the read-only R3B presentation service."""

import json
import inspect
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.business_decision_plan import BusinessDecisionPlanService
from app.application.business_workflow_presentation import (
    BusinessWorkflowPresentationNotFoundError,
    BusinessWorkflowPresentationService,
)
import app.application.business_workflow_presentation as presentation_module
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.database import SessionLocal
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.runtime import RuntimeExecution, RuntimeResultReference
from app.schemas.business_workflow_presentation import (
    BusinessWorkflowDecisionPresentationResponse,
    ExecutionPresentation,
)


MANIFEST = Path(__file__).with_name(".fu_f6a_r3_b_presentation_service.json")
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
    raise AssertionError("presentation read invoked forbidden computation")


def _counts(session):
    return {
        "runtime_executions": session.query(RuntimeExecution).filter_by(company_id=COMPANY_ID).count(),
        "runtime_result_references": session.query(RuntimeResultReference).filter_by(company_id=COMPANY_ID).count(),
        "decision_finalizations": session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=COMPANY_ID).count(),
        "associations": session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=COMPANY_ID).count(),
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=COMPANY_ID).count(),
        "candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(
            DecisionSnapshot.company_id == COMPANY_ID
        ).count(),
        "feedback": session.query(DecisionFeedbackEvent).filter_by(company_id=COMPANY_ID).count(),
    }


def _contract_nullability_smoke():
    execution = ExecutionPresentation(
        execution_id=uuid4(), status="running", progress=0.0, current_stage="forecast",
        created_at=datetime.now(timezone.utc), started_at=None, completed_at=None,
        dataset_id=uuid4(), workflow_id="business_workflow", failure_summary=None,
    )
    pending = BusinessWorkflowDecisionPresentationResponse(
        execution=execution, aggregate=None, decision_finalization=None, decisions=(),
    )
    assert pending.aggregate is None and pending.decision_finalization is None and pending.decisions == ()


def main():
    _contract_nullability_smoke()
    source = inspect.getsource(presentation_module)
    for forbidden_dependency in (
        "BusinessDecisionPlanService", "DecisionEvidenceResolver", "DecisionPolicy",
        "ForecastExecutor", "SafetyStockExecutor", "SimulationExecutor", "BacktestExecutor",
        "SupplierExecutor", "Learning",
    ):
        assert forbidden_dependency not in source, forbidden_dependency
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        before = _counts(session)
    finally:
        session.rollback()
        session.close()

    with patch.object(BusinessDecisionPlanService, "materialize", _forbidden), \
         patch.object(DecisionEvidenceResolver, "resolve", _forbidden), \
         patch.object(DecisionPolicy, "evaluate", _forbidden):
        response = BusinessWorkflowPresentationService().get(COMPANY_ID, EXECUTION_ID)

    assert response.execution.execution_id == EXECUTION_ID
    assert response.execution.status == "completed"
    assert response.aggregate is not None
    assert response.aggregate.result_reference_id == AGGREGATE_ID
    assert response.aggregate.result_type == "business_workflow"
    assert response.aggregate.available_result_types == ("backtest", "forecast", "safety_stock", "simulation")
    assert response.decision_finalization is not None
    # R2-E recovered its intentionally limited second SKU; retained persisted
    # truth is therefore terminal success, not the earlier partial checkpoint.
    assert response.decision_finalization.status == "succeeded"
    assert response.decision_finalization.completed_material_codes == ("SKU-A", "SKU-B")
    assert response.decision_finalization.limitations == ()
    assert tuple(item.association.id for item in response.decisions) == EXPECTED_ASSOCIATIONS
    assert tuple(item.snapshot.id for item in response.decisions) == EXPECTED_SNAPSHOTS
    assert tuple(item.association.material_code for item in response.decisions) == ("SKU-A", "SKU-B")
    assert all(tuple(candidate.ordinal for candidate in item.candidates) == tuple(sorted(candidate.ordinal for candidate in item.candidates)) for item in response.decisions)
    assert all(item.explanation.explanation_fingerprint for item in response.decisions)

    try:
        BusinessWorkflowPresentationService().get(uuid4(), EXECUTION_ID)
    except BusinessWorkflowPresentationNotFoundError:
        pass
    else:
        raise AssertionError("foreign company lookup must not expose the execution")

    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        after = _counts(session)
    finally:
        session.rollback()
        session.close()
    assert before == after

    manifest = {
        "company_id": str(COMPANY_ID),
        "execution_id": str(EXECUTION_ID),
        "aggregate_result_reference_id": str(AGGREGATE_ID),
        "association_ids": [str(value) for value in EXPECTED_ASSOCIATIONS],
        "snapshot_ids": [str(value) for value in EXPECTED_SNAPSHOTS],
        "decision_count": len(response.decisions),
        "full_aggregate_embedded": False,
        "deterministic_ordering": True,
        "no_materialize": True,
        "no_resolver": True,
        "no_policy": True,
        "no_current_learning": True,
        "no_analytics": True,
        "database_writes": 0,
        "before_counts": before,
        "after_counts": after,
        "dto_module": "app.schemas.business_workflow_presentation",
        "service_module": "app.application.business_workflow_presentation",
    }
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
    assert json.loads(MANIFEST.read_text(encoding="utf-8")) == manifest
    print("R3B_PRESENTATION", json.dumps(manifest, sort_keys=True))
    print("FU_F6A_R3B_PRESENTATION_SERVICE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
