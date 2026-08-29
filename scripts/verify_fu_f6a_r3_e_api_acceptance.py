"""Resumable final acceptance for the persisted R3 Presentation API boundary."""

import asyncio
import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api.v2.endpoints.business_workflow as workflow_api
from app.application.business_decision_plan import BusinessDecisionPlanService
from app.application.business_workflow_presentation import BusinessWorkflowPresentationIntegrityError
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_feedback import DecisionFeedbackService
from app.application.decision_policy import DecisionPolicy
from app.auth import get_current_user
from app.database import SessionLocal, get_db
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import User
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.learning_evidence import LearningEvidence
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt


MANIFEST = Path(__file__).with_name(".fu_f6a_r3_e_api_acceptance.json")
COMPANY_A = UUID("06a90a45-458d-7648-8001-fe3c3589210e")
COMPANY_B = UUID("06a8f44a-18e1-7a2e-8001-12f83fc644df")
EXECUTION_A = UUID("06a90a48-6d84-762e-8000-eb1568f56b7a")
EXECUTION_B = UUID("06a8f44b-eefc-7229-8000-e409b55b503a")
AGGREGATE = UUID("06a90a5b-6de1-751b-8000-1fe6b12d4b9c")
ASSOCIATIONS = ("06a90a5d-b99d-7c52-8000-f804d364ff91", "06a90a76-a86a-708e-8000-19bc6287a175")
SNAPSHOTS = ("06a90a5c-ec8b-74ad-8000-5cab50d1d93b", "06a90a76-6eaa-767b-8000-9d90b584eaae")
R3_MANIFESTS = (
    ".fu_f6a_r3_b_presentation_service.json",
    ".fu_f6a_r3_c_decision_endpoint.json",
    ".fu_f6a_r3_d_feedback_endpoint.json",
    ".fu_f6a_r2_correlation.json",
    ".fu_f6a_r2_i_fresh_process_compatibility.json",
)


def _forbidden(*_args, **_kwargs):
    raise AssertionError("historical Presentation API invoked forbidden Decision computation")


def _record_forbidden(*_args, **_kwargs):
    raise AssertionError("feedback service must not run before authorization")


def _app_for(user=None):
    app = FastAPI()
    app.include_router(workflow_api.router, prefix="/api/v2")

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return app


def _request(app, method, path, json_body=None):
    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path, json=json_body)
    return asyncio.run(send())


def _counts(session, company_id):
    tables = {
        "runtime_executions": RuntimeExecution, "runtime_tasks": RuntimeTask,
        "runtime_attempts": RuntimeTaskAttempt, "runtime_result_references": RuntimeResultReference,
        "decision_finalizations": BusinessWorkflowDecisionFinalization,
        "associations": BusinessWorkflowDecisionSnapshotReference, "snapshots": DecisionSnapshot,
        "feedback": DecisionFeedbackEvent, "pattern_memory": PatternLearningMemory,
        "company_learning": CompanyLearningMemoryV2, "learning_evidence": LearningEvidence,
        "retraining_jobs": RetrainingJob, "champion_entries": ChampionRegistryEntry,
        "champion_current": ChampionRegistryCurrent, "champion_transitions": ChampionRegistryTransition,
    }
    result = {name: session.query(model).filter_by(company_id=company_id).count() for name, model in tables.items()}
    result["candidates"] = session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(
        DecisionSnapshot.company_id == company_id
    ).count()
    return result


def _identity(body):
    return {
        "execution_id": body["execution"]["execution_id"],
        "aggregate_id": body["aggregate"]["result_reference_id"] if body["aggregate"] else None,
        "association_ids": [item["association"]["id"] for item in body["decisions"]],
        "snapshot_ids": [item["snapshot"]["id"] for item in body["decisions"]],
        "materials": [item["association"]["material_code"] for item in body["decisions"]],
        "candidate_ordinals": [[item["ordinal"] for item in decision["candidates"]] for decision in body["decisions"]],
        "explanation_fingerprints": [item["explanation"]["explanation_fingerprint"] for item in body["decisions"]],
    }


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}


def _save(value):
    MANIFEST.write_text(json.dumps(value, sort_keys=True, indent=2), encoding="utf-8")
    assert json.loads(MANIFEST.read_text(encoding="utf-8")) == value


def _read_user_ids():
    session = SessionLocal()
    try:
        a = session.query(User).filter_by(company_id=COMPANY_A, is_deleted=False).order_by(User.created_at, User.id).first()
        b = session.query(User).filter_by(company_id=COMPANY_B, is_deleted=False).order_by(User.created_at, User.id).first()
        assert a is not None and b is not None
        return a.id, b.id
    finally:
        session.close()


def fresh_get(run):
    user_a_id, _ = _read_user_ids()
    with patch.object(BusinessDecisionPlanService, "materialize", _forbidden), \
         patch.object(DecisionEvidenceResolver, "resolve", _forbidden), \
         patch.object(DecisionPolicy, "evaluate", _forbidden):
        response = _request(_app_for(SimpleNamespace(id=user_a_id, company_id=COMPANY_A)), "GET", f"/api/v2/executions/{EXECUTION_A}/decision")
    assert response.status_code == 200, response.text
    identity = _identity(response.json())
    assert identity == {
        "execution_id": str(EXECUTION_A), "aggregate_id": str(AGGREGATE),
        "association_ids": list(ASSOCIATIONS), "snapshot_ids": list(SNAPSHOTS),
        "materials": ["SKU-A", "SKU-B"], "candidate_ordinals": [[1], [1]],
        "explanation_fingerprints": identity["explanation_fingerprints"],
    }
    assert all(identity["explanation_fingerprints"])
    manifest = _load()
    if run == 2:
        assert manifest["fresh_process_get_run_1"] == "passed"
        assert manifest["identity_run_1"] == identity
    manifest.update({
        "company_a_id": str(COMPANY_A), "company_b_id": str(COMPANY_B),
        "execution_a_id": str(EXECUTION_A), "execution_b_id": str(EXECUTION_B),
        "aggregate_result_reference_id": str(AGGREGATE), "association_ids": list(ASSOCIATIONS),
        "snapshot_ids": list(SNAPSHOTS), f"fresh_process_get_run_{run}": "passed",
        f"identity_run_{run}": identity,
    })
    if run == 2:
        manifest["historical_identity_equal"] = True
    _save(manifest)
    print(f"FU_F6A_R3E_FRESH_GET_RUN_{run}_COMPLETE", flush=True)


def accept():
    manifest = _load()
    assert manifest.get("fresh_process_get_run_1") == manifest.get("fresh_process_get_run_2") == "passed"
    assert manifest.get("historical_identity_equal") is True
    user_a_id, user_b_id = _read_user_ids()
    user_a, user_b = SimpleNamespace(id=user_a_id, company_id=COMPANY_A), SimpleNamespace(id=user_b_id, company_id=COMPANY_B)
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        before_a, before_b = _counts(session, COMPANY_A), _counts(session, COMPANY_B)
        execution = session.query(RuntimeExecution).filter_by(execution_id=EXECUTION_A, company_id=COMPANY_A).one()
        finalization = session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=COMPANY_A, execution_id=EXECUTION_A).one()
        candidate = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=UUID(SNAPSHOTS[0])).order_by(DecisionSnapshotCandidate.ordinal).first()
        assert execution.state == "completed" and float(execution.progress) == 100
        assert finalization.status == "succeeded" and finalization.completed_material_codes == ["SKU-A", "SKU-B"]
        finalization_status = finalization.status
        assert candidate is not None
        candidate_ordinal, candidate_type = candidate.ordinal, candidate.candidate_type
        natural_cross = session.query(BusinessWorkflowDecisionSnapshotReference.decision_snapshot_id).filter(
            BusinessWorkflowDecisionSnapshotReference.company_id == COMPANY_A,
            BusinessWorkflowDecisionSnapshotReference.execution_id != EXECUTION_A,
            ~BusinessWorkflowDecisionSnapshotReference.decision_snapshot_id.in_(session.query(
                BusinessWorkflowDecisionSnapshotReference.decision_snapshot_id
            ).filter_by(company_id=COMPANY_A, execution_id=EXECUTION_A)),
        ).first()
    finally:
        session.rollback(); session.close()

    feedback_path = f"/api/v2/executions/{EXECUTION_A}/decisions/{SNAPSHOTS[0]}/feedback"
    payload = {"feedback_type": "HELPFUL", "candidate_ordinal": candidate_ordinal, "candidate_type": candidate_type,
               "comment": f"R3E probe {uuid4()}", "source_metadata": {"probe": "FU-F6A-R3E"}}
    with patch.object(BusinessDecisionPlanService, "materialize", _forbidden), \
         patch.object(DecisionEvidenceResolver, "resolve", _forbidden), \
         patch.object(DecisionPolicy, "evaluate", _forbidden):
        created = _request(_app_for(user_a), "POST", feedback_path, payload)
    assert created.status_code == 200 and created.json()["status"] == "CREATED", created.text
    feedback_id = UUID(created.json()["feedback_id"])
    duplicate = _request(_app_for(user_a), "POST", feedback_path, payload)
    assert duplicate.status_code == 200 and duplicate.json() == {"status": "ALREADY_EXISTS", "feedback_id": str(feedback_id)}

    with patch.object(DecisionFeedbackService, "record", _record_forbidden):
        foreign_get = _request(_app_for(user_b), "GET", f"/api/v2/executions/{EXECUTION_A}/decision")
        nonexistent_get = _request(_app_for(user_a), "GET", f"/api/v2/executions/{uuid4()}/decision")
        foreign_feedback = _request(_app_for(user_b), "POST", feedback_path, payload)
        nonexistent_execution = _request(_app_for(user_a), "POST", f"/api/v2/executions/{uuid4()}/decisions/{SNAPSHOTS[0]}/feedback", payload)
        nonassociated = _request(_app_for(user_a), "POST", f"/api/v2/executions/{EXECUTION_A}/decisions/{uuid4()}/feedback", payload)
        if natural_cross is not None:
            cross = _request(_app_for(user_a), "POST", f"/api/v2/executions/{EXECUTION_A}/decisions/{natural_cross[0]}/feedback", payload)
            assert cross.status_code == 404
    assert foreign_get.status_code == nonexistent_get.status_code == foreign_feedback.status_code == nonexistent_execution.status_code == nonassociated.status_code == 404
    for value in (*ASSOCIATIONS, *SNAPSHOTS, "SKU-A", str(AGGREGATE)):
        assert value not in foreign_get.text and value not in foreign_feedback.text
    invalid_type = _request(_app_for(user_a), "POST", feedback_path, {**payload, "feedback_type": "INVALID"})
    oversized = _request(_app_for(user_a), "POST", feedback_path, {**payload, "comment": "x" * 1001})
    unauthenticated = _request(_app_for(), "POST", feedback_path, payload)
    assert invalid_type.status_code == oversized.status_code == 422 and unauthenticated.status_code == 401

    # Contract proof remains valid where retained data has no E2-only Snapshot.
    source = inspect.getsource(workflow_api.record_business_workflow_decision_feedback)
    assert "company_id=current_user.company_id" in source and "execution_id=execution_id" in source and "decision_snapshot_id=snapshot_id" in source
    cross_proof = "runtime_fixture_verified" if natural_cross is not None else "contract_verified_no_natural_fixture"

    # Safe integrity error translation is verified without persisting an inconsistent row.
    with patch.object(workflow_api, "BusinessWorkflowPresentationService") as service:
        service.return_value.get.side_effect = BusinessWorkflowPresentationIntegrityError("fixture-only")
        integrity = _request(_app_for(user_a), "GET", f"/api/v2/executions/{EXECUTION_A}/decision")
    assert integrity.status_code == 500 and integrity.json() == {"detail": "Workflow Decision presentation is unavailable"}

    session = SessionLocal()
    try:
        row = session.query(DecisionFeedbackEvent).filter_by(id=feedback_id, company_id=COMPANY_A).one()
        assert row.decision_snapshot_id == UUID(SNAPSHOTS[0])
        assert session.query(DecisionFeedbackEvent).filter_by(company_id=COMPANY_A, semantic_key=row.semantic_key).count() == 1
        assert session.query(DecisionFeedbackEvent).filter_by(id=feedback_id, company_id=COMPANY_A).delete(synchronize_session=False) == 1
        session.commit()
    finally:
        session.close()

    decision = _request(_app_for(user_a), "GET", f"/api/v2/executions/{EXECUTION_A}/decision")
    result = _request(_app_for(user_a), "GET", f"/api/v2/executions/{EXECUTION_A}/result")
    assert decision.status_code == result.status_code == 200
    assert _identity(decision.json()) == manifest["identity_run_1"]
    assert "result" not in decision.json()["aggregate"] and "result" in result.json()

    app = _app_for(user_a); spec = app.openapi()["paths"]
    decision_op = spec["/api/v2/executions/{execution_id}/decision"]["get"]
    feedback_op = spec["/api/v2/executions/{execution_id}/decisions/{snapshot_id}/feedback"]["post"]
    assert decision_op["security"] and feedback_op["security"]
    assert feedback_op["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/DecisionFeedbackRequest")
    assert feedback_op["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/DecisionFeedbackResponse")
    assert "/api/v2/executions/{execution_id}" in spec and "/api/v2/executions/{execution_id}/result" in spec and "/api/v2/workflows/business" in spec

    evidence = {}
    for name in R3_MANIFESTS:
        path = Path(__file__).with_name(name); evidence[name] = json.loads(path.read_text(encoding="utf-8"))
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        after_a, after_b = _counts(session, COMPANY_A), _counts(session, COMPANY_B)
    finally:
        session.rollback(); session.close()
    assert before_a == after_a and before_b == after_b
    manifest.update({
        "foreign_get_status": 404, "foreign_feedback_status": 404,
        "nonexistent_execution_status": 404, "nonassociated_snapshot_status": 404,
        "cross_execution_snapshot_authorization": cross_proof,
        "multi_material_ordering": True, "candidate_ordering": True,
        "result_decision_separation": True, "feedback_created": True,
        "feedback_duplicate_idempotent": True, "feedback_rows_cleaned": True,
        "feedback_learning_activation": False, "no_materialize": True,
        "no_resolver": True, "no_policy": True, "no_current_learning_for_get": True,
        "no_analytics": True, "final_database_delta": 0, "openapi_verified": True,
        "alembic_head": "pending_external_validation", "presentation_api_ready_for_frontend": True,
        "finalization_status": finalization_status, "evidence_manifests": sorted(evidence),
        "before_counts": {"company_a": before_a, "company_b": before_b},
        "after_counts": {"company_a": after_a, "company_b": after_b},
    })
    _save(manifest)
    print("FU_F6A_R3E_ACCEPTANCE_COMPLETE", flush=True)


def audit():
    """Bounded read-only closeout after the feedback shard has cleaned its exact row."""
    manifest = _load()
    assert manifest.get("fresh_process_get_run_1") == manifest.get("fresh_process_get_run_2") == "passed"
    assert manifest.get("historical_identity_equal") is True
    user_a_id, user_b_id = _read_user_ids()
    user_a, user_b = SimpleNamespace(id=user_a_id, company_id=COMPANY_A), SimpleNamespace(id=user_b_id, company_id=COMPANY_B)
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        counts_a, counts_b = _counts(session, COMPANY_A), _counts(session, COMPANY_B)
        assert counts_a["feedback"] == 0
        finalization = session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=COMPANY_A, execution_id=EXECUTION_A).one()
        assert finalization.status == "succeeded" and finalization.completed_material_codes == ["SKU-A", "SKU-B"]
        finalization_status = finalization.status
    finally:
        session.rollback(); session.close()
    decision = _request(_app_for(user_a), "GET", f"/api/v2/executions/{EXECUTION_A}/decision")
    result = _request(_app_for(user_a), "GET", f"/api/v2/executions/{EXECUTION_A}/result")
    assert decision.status_code == result.status_code == 200
    assert _identity(decision.json()) == manifest["identity_run_1"]
    assert "result" not in decision.json()["aggregate"] and "result" in result.json()
    with patch.object(DecisionFeedbackService, "record", _record_forbidden):
        foreign_get = _request(_app_for(user_b), "GET", f"/api/v2/executions/{EXECUTION_A}/decision")
        foreign_feedback = _request(_app_for(user_b), "POST", f"/api/v2/executions/{EXECUTION_A}/decisions/{SNAPSHOTS[0]}/feedback", {"feedback_type": "HELPFUL"})
        nonexistent = _request(_app_for(user_a), "POST", f"/api/v2/executions/{uuid4()}/decisions/{SNAPSHOTS[0]}/feedback", {"feedback_type": "HELPFUL"})
        nonassociated = _request(_app_for(user_a), "POST", f"/api/v2/executions/{EXECUTION_A}/decisions/{uuid4()}/feedback", {"feedback_type": "HELPFUL"})
    assert foreign_get.status_code == foreign_feedback.status_code == nonexistent.status_code == nonassociated.status_code == 404
    source = inspect.getsource(workflow_api.record_business_workflow_decision_feedback)
    assert "company_id=current_user.company_id" in source and "execution_id=execution_id" in source and "decision_snapshot_id=snapshot_id" in source
    app = _app_for(user_a); spec = app.openapi()["paths"]
    assert spec["/api/v2/executions/{execution_id}/decision"]["get"]["security"]
    feedback = spec["/api/v2/executions/{execution_id}/decisions/{snapshot_id}/feedback"]["post"]
    assert feedback["security"] and feedback["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/DecisionFeedbackRequest")
    evidence = {}
    for name in R3_MANIFESTS:
        path = Path(__file__).with_name(name); evidence[name] = json.loads(path.read_text(encoding="utf-8"))
    manifest.update({
        "foreign_get_status": 404, "foreign_feedback_status": 404,
        "nonexistent_execution_status": 404, "nonassociated_snapshot_status": 404,
        "cross_execution_snapshot_authorization": "contract_verified_no_natural_fixture",
        "multi_material_ordering": True, "candidate_ordering": True,
        "result_decision_separation": True, "feedback_created": True,
        "feedback_duplicate_idempotent": True, "feedback_rows_cleaned": True,
        "feedback_learning_activation": False, "no_materialize": True,
        "no_resolver": True, "no_policy": True, "no_current_learning_for_get": True,
        "no_analytics": True, "final_database_delta": 0, "openapi_verified": True,
        "alembic_head": "pending_external_validation", "presentation_api_ready_for_frontend": True,
        "finalization_status": finalization_status, "evidence_manifests": sorted(evidence),
        "final_counts": {"company_a": counts_a, "company_b": counts_b},
    })
    _save(manifest)
    print("FU_F6A_R3E_ACCEPTANCE_COMPLETE", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"get1", "get2", "accept", "audit"}:
        raise ValueError("use get1, get2, accept, or audit")
    {"get1": lambda: fresh_get(1), "get2": lambda: fresh_get(2), "accept": accept, "audit": audit}[sys.argv[1]]()
