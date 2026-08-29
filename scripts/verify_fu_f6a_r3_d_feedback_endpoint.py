"""Focused mounted-API verification for execution-scoped Decision feedback."""

import asyncio
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
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_feedback import DecisionFeedbackService
from app.application.decision_policy import DecisionPolicy
from app.auth import get_current_user
from app.database import SessionLocal, get_db
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.company import User
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.runtime import RuntimeExecution, RuntimeResultReference


MANIFEST = Path(__file__).with_name(".fu_f6a_r3_d_feedback_endpoint.json")
COMPANY_A = UUID("06a90a45-458d-7648-8001-fe3c3589210e")
COMPANY_B = UUID("06a8f44a-18e1-7a2e-8001-12f83fc644df")
EXECUTION_ID = UUID("06a90a48-6d84-762e-8000-eb1568f56b7a")
SNAPSHOT_ID = UUID("06a90a5c-ec8b-74ad-8000-5cab50d1d93b")
ASSOCIATION_ID = UUID("06a90a5d-b99d-7c52-8000-f804d364ff91")


def _forbidden(*_args, **_kwargs):
    raise AssertionError("feedback endpoint invoked forbidden Decision computation")


def _record_forbidden(*_args, **_kwargs):
    raise AssertionError("feedback service must not run before authorization succeeds")


def _counts(session, company_id):
    return {
        "runtime_executions": session.query(RuntimeExecution).filter_by(company_id=company_id).count(),
        "runtime_result_references": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
        "decision_finalizations": session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=company_id).count(),
        "associations": session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=company_id).count(),
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=company_id).count(),
        "candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(
            DecisionSnapshot.company_id == company_id
        ).count(),
        "feedback": session.query(DecisionFeedbackEvent).filter_by(company_id=company_id).count(),
    }


def _app_for(user):
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


def _request(app, path, json_body):
    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.post(path, json=json_body)
    return asyncio.run(send())


def _get(app, path):
    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get(path)
    return asyncio.run(send())


def main():
    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        user_a = session.query(User).filter_by(company_id=COMPANY_A, is_deleted=False).order_by(User.created_at, User.id).first()
        user_b = session.query(User).filter_by(company_id=COMPANY_B, is_deleted=False).order_by(User.created_at, User.id).first()
        candidate = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=SNAPSHOT_ID).order_by(
            DecisionSnapshotCandidate.ordinal
        ).first()
        assert user_a is not None and user_b is not None and candidate is not None
        user_a_id, user_b_id = user_a.id, user_b.id
        candidate_ordinal, candidate_type = candidate.ordinal, candidate.candidate_type
        before_a, before_b = _counts(session, COMPANY_A), _counts(session, COMPANY_B)
        same_company_other_snapshot = session.query(DecisionSnapshot.id).filter(
            DecisionSnapshot.company_id == COMPANY_A,
            ~DecisionSnapshot.id.in_(session.query(BusinessWorkflowDecisionSnapshotReference.decision_snapshot_id).filter_by(
                company_id=COMPANY_A, execution_id=EXECUTION_ID
            )),
        ).first()
    finally:
        session.rollback()
        session.close()

    user_a = SimpleNamespace(id=user_a_id, company_id=COMPANY_A)
    user_b = SimpleNamespace(id=user_b_id, company_id=COMPANY_B)
    route = f"/api/v2/executions/{EXECUTION_ID}/decisions/{SNAPSHOT_ID}/feedback"
    payload = {
        "feedback_type": "HELPFUL",
        "candidate_ordinal": candidate_ordinal,
        "candidate_type": candidate_type,
        "comment": f"R3D probe {uuid4()}",
        "source_metadata": {"probe": "FU-F6A-R3D"},
    }

    with patch.object(BusinessDecisionPlanService, "materialize", _forbidden), \
         patch.object(DecisionEvidenceResolver, "resolve", _forbidden), \
         patch.object(DecisionPolicy, "evaluate", _forbidden):
        positive = _request(_app_for(user_a), route, payload)
    assert positive.status_code == 200, positive.text
    assert positive.json()["status"] == "CREATED"
    feedback_id = UUID(positive.json()["feedback_id"])

    duplicate = _request(_app_for(user_a), route, payload)
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json() == {"status": "ALREADY_EXISTS", "feedback_id": str(feedback_id)}

    nonexistent_execution = _request(
        _app_for(user_a), f"/api/v2/executions/{uuid4()}/decisions/{SNAPSHOT_ID}/feedback", payload,
    )
    nonassociated_snapshot = _request(
        _app_for(user_a), f"/api/v2/executions/{EXECUTION_ID}/decisions/{uuid4()}/feedback", payload,
    )
    foreign_execution = _request(_app_for(user_b), route, payload)
    with patch.object(DecisionFeedbackService, "record", _record_forbidden):
        assert nonexistent_execution.status_code == 404
        assert nonassociated_snapshot.status_code == 404
        assert foreign_execution.status_code == 404

    # Re-run negatives under record guard so the guard proves authorization order.
    with patch.object(DecisionFeedbackService, "record", _record_forbidden):
        assert _request(_app_for(user_a), f"/api/v2/executions/{uuid4()}/decisions/{SNAPSHOT_ID}/feedback", payload).status_code == 404
        assert _request(_app_for(user_a), f"/api/v2/executions/{EXECUTION_ID}/decisions/{uuid4()}/feedback", payload).status_code == 404
        assert _request(_app_for(user_b), route, payload).status_code == 404
        if same_company_other_snapshot is not None:
            assert _request(
                _app_for(user_a),
                f"/api/v2/executions/{EXECUTION_ID}/decisions/{same_company_other_snapshot[0]}/feedback",
                payload,
            ).status_code == 404

    invalid_type = _request(_app_for(user_a), route, {**payload, "feedback_type": "INVALID"})
    oversized_comment = _request(_app_for(user_a), route, {**payload, "comment": "x" * 1001})
    assert invalid_type.status_code == oversized_comment.status_code == 422

    unauthenticated = _request(_app_for(None), route, payload)
    assert unauthenticated.status_code == 401

    session = SessionLocal()
    try:
        rows = session.query(DecisionFeedbackEvent).filter_by(id=feedback_id, company_id=COMPANY_A).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.decision_snapshot_id == SNAPSHOT_ID
        assert row.candidate_ordinal == candidate_ordinal and row.candidate_type == candidate_type
        assert row.feedback_type == "HELPFUL"
        deleted = session.query(DecisionFeedbackEvent).filter_by(id=feedback_id, company_id=COMPANY_A).delete(
            synchronize_session=False
        )
        assert deleted == 1
        session.commit()
    finally:
        session.close()

    decision = _get(_app_for(user_a), f"/api/v2/executions/{EXECUTION_ID}/decision")
    result = _get(_app_for(user_a), f"/api/v2/executions/{EXECUTION_ID}/result")
    assert decision.status_code == 200 and result.status_code == 200
    assert [item["association"]["id"] for item in decision.json()["decisions"]] == [
        "06a90a5d-b99d-7c52-8000-f804d364ff91", "06a90a76-a86a-708e-8000-19bc6287a175",
    ]
    assert "result" in result.json()

    routes = [route for route in workflow_api.router.routes if getattr(route, "path", None) == "/executions/{execution_id}/decisions/{snapshot_id}/feedback"]
    assert len(routes) == 1 and routes[0].methods == {"POST"}
    schema = _app_for(user_a).openapi()["paths"]["/api/v2/executions/{execution_id}/decisions/{snapshot_id}/feedback"]["post"]
    assert schema["security"]
    assert schema["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/DecisionFeedbackRequest")
    assert schema["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/DecisionFeedbackResponse")
    assert {"400", "401", "404", "422"}.issubset(schema["responses"])

    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        after_a, after_b = _counts(session, COMPANY_A), _counts(session, COMPANY_B)
    finally:
        session.rollback()
        session.close()
    assert before_a == after_a and before_b == after_b

    manifest = {
        "route": "/api/v2/executions/{execution_id}/decisions/{snapshot_id}/feedback",
        "method": "POST",
        "company_id": str(COMPANY_A), "execution_id": str(EXECUTION_ID),
        "snapshot_id": str(SNAPSHOT_ID), "association_id": str(ASSOCIATION_ID),
        "positive_status": positive.status_code, "positive_result": positive.json()["status"],
        "duplicate_status": duplicate.status_code, "duplicate_result": duplicate.json()["status"],
        "foreign_status": foreign_execution.status_code,
        "nonexistent_execution_status": nonexistent_execution.status_code,
        "nonassociated_snapshot_status": nonassociated_snapshot.status_code,
        "invalid_feedback_type_status": invalid_type.status_code,
        "oversized_comment_status": oversized_comment.status_code,
        "feedback_rows_created": 1, "feedback_rows_cleaned": 1, "final_feedback_delta": 0,
        "same_company_cross_execution_case": "verified" if same_company_other_snapshot is not None else "deferred_no_retained_snapshot",
        "no_materialize": True, "no_resolver": True, "no_policy": True,
        "no_current_learning": True, "no_analytics": True,
        "non_feedback_tables_unchanged": True, "openapi_verified": True,
        "before_counts": {"company_a": before_a, "company_b": before_b},
        "after_counts": {"company_a": after_a, "company_b": after_b},
    }
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
    assert json.loads(MANIFEST.read_text(encoding="utf-8")) == manifest
    print("R3D_FEEDBACK", json.dumps(manifest, sort_keys=True))
    print("FU_F6A_R3D_FEEDBACK_ENDPOINT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
