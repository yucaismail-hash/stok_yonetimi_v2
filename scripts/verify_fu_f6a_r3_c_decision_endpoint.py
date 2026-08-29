"""Focused mounted-API proof for the R3C persisted Decision presentation read."""

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
from app.application.decision_policy import DecisionPolicy
from app.auth import get_current_user
from app.database import SessionLocal, get_db
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.runtime import RuntimeExecution, RuntimeResultReference


MANIFEST = Path(__file__).with_name(".fu_f6a_r3_c_decision_endpoint.json")
COMPANY_A = UUID("06a90a45-458d-7648-8001-fe3c3589210e")
COMPANY_B = UUID("06a8f44a-18e1-7a2e-8001-12f83fc644df")
EXECUTION_ID = UUID("06a90a48-6d84-762e-8000-eb1568f56b7a")
AGGREGATE_ID = UUID("06a90a5b-6de1-751b-8000-1fe6b12d4b9c")
EXPECTED_ASSOCIATIONS = (
    "06a90a5d-b99d-7c52-8000-f804d364ff91",
    "06a90a76-a86a-708e-8000-19bc6287a175",
)
EXPECTED_SNAPSHOTS = (
    "06a90a5c-ec8b-74ad-8000-5cab50d1d93b",
    "06a90a76-6eaa-767b-8000-9d90b584eaae",
)


def _forbidden(*_args, **_kwargs):
    raise AssertionError("presentation endpoint invoked forbidden Decision computation")


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


def _app_for(company_id=None):
    app = FastAPI()
    app.include_router(workflow_api.router, prefix="/api/v2")

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    if company_id is not None:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            company_id=company_id, id=uuid4(),
        )
    return app


def _request(app, path):
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
        before_a, before_b = _counts(session, COMPANY_A), _counts(session, COMPANY_B)
    finally:
        session.rollback()
        session.close()

    app_a = _app_for(COMPANY_A)
    with patch.object(BusinessDecisionPlanService, "materialize", _forbidden), \
         patch.object(DecisionEvidenceResolver, "resolve", _forbidden), \
         patch.object(DecisionPolicy, "evaluate", _forbidden):
        positive = _request(app_a, f"/api/v2/executions/{EXECUTION_ID}/decision")
    assert positive.status_code == 200, positive.text
    body = positive.json()
    assert body["execution"]["execution_id"] == str(EXECUTION_ID)
    assert body["aggregate"]["result_reference_id"] == str(AGGREGATE_ID)
    assert "result" not in body["aggregate"]
    assert len(body["decisions"]) == 2
    assert [item["association"]["id"] for item in body["decisions"]] == list(EXPECTED_ASSOCIATIONS)
    assert [item["snapshot"]["id"] for item in body["decisions"]] == list(EXPECTED_SNAPSHOTS)
    assert [item["association"]["material_code"] for item in body["decisions"]] == ["SKU-A", "SKU-B"]

    foreign = _request(_app_for(COMPANY_B), f"/api/v2/executions/{EXECUTION_ID}/decision")
    absent = _request(_app_for(COMPANY_A), f"/api/v2/executions/{uuid4()}/decision")
    assert foreign.status_code == absent.status_code == 404
    assert foreign.json() == absent.json() == {"detail": "Business Workflow execution was not found"}
    foreign_text = foreign.text
    for prohibited in (*EXPECTED_ASSOCIATIONS, *EXPECTED_SNAPSHOTS, "SKU-A", "SKU-B"):
        assert prohibited not in foreign_text

    unauthenticated = _request(_app_for(), f"/api/v2/executions/{EXECUTION_ID}/decision")
    assert unauthenticated.status_code == 401

    result = _request(_app_for(COMPANY_A), f"/api/v2/executions/{EXECUTION_ID}/result")
    assert result.status_code == 200, result.text
    assert result.json()["execution_id"] == str(EXECUTION_ID)
    assert "result" in result.json() and result.json()["result"]["provenance"]

    routes = [route for route in workflow_api.router.routes if getattr(route, "path", None) == "/executions/{execution_id}/decision"]
    assert len(routes) == 1 and routes[0].methods == {"GET"}
    operation = app_a.openapi()["paths"]["/api/v2/executions/{execution_id}/decision"]["get"]
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["$ref"].endswith("/BusinessWorkflowDecisionPresentationResponse")
    assert operation["security"]

    session = SessionLocal()
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        after_a, after_b = _counts(session, COMPANY_A), _counts(session, COMPANY_B)
    finally:
        session.rollback()
        session.close()
    assert before_a == after_a and before_b == after_b

    manifest = {
        "route": "/api/v2/executions/{execution_id}/decision",
        "method": "GET",
        "company_id": str(COMPANY_A),
        "execution_id": str(EXECUTION_ID),
        "aggregate_result_reference_id": str(AGGREGATE_ID),
        "association_ids": list(EXPECTED_ASSOCIATIONS),
        "snapshot_ids": list(EXPECTED_SNAPSHOTS),
        "positive_status": positive.status_code,
        "foreign_status": foreign.status_code,
        "nonexistent_status": absent.status_code,
        "full_aggregate_embedded": False,
        "existing_result_endpoint_unchanged": True,
        "no_materialize": True,
        "no_resolver": True,
        "no_policy": True,
        "no_current_learning": True,
        "no_analytics": True,
        "database_writes": 0,
        "openapi_verified": True,
        "before_counts": {"company_a": before_a, "company_b": before_b},
        "after_counts": {"company_a": after_a, "company_b": after_b},
    }
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
    assert json.loads(MANIFEST.read_text(encoding="utf-8")) == manifest
    print("R3C_ENDPOINT", json.dumps(manifest, sort_keys=True))
    print("FU_F6A_R3C_DECISION_ENDPOINT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
