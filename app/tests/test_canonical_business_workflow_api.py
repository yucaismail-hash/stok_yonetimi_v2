import asyncio
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi import FastAPI

import app.api.v2.endpoints.business_workflow as workflow_api
from app.application.canonical_business_workflow import (
    WorkflowDatasetUnavailableError,
    WorkflowReadinessBlockedError,
    WorkflowNotFoundError,
    WorkflowResultNotReadyError,
)
from app.application.business_workflow_readiness import BusinessWorkflowReadiness, CapabilityReadiness
from app.auth import get_current_user
from app.database import get_db


COMPANY_ID, USER_ID, DATASET_ID, EXECUTION_ID = (uuid4() for _ in range(4))
NOW = datetime.now(timezone.utc)


def _execution(**overrides):
    values = {
        "execution_id": EXECUTION_ID, "company_id": COMPANY_ID, "user_id": USER_ID,
        "dataset_id": DATASET_ID, "workflow_id": "business-test",
        "analysis_type": "business_workflow", "state": "queued", "progress": 0,
        "current_stage": "planning", "created_at": NOW, "started_at": None,
        "completed_at": None, "terminal_error": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class StubWorkflowService:
    mode = "ok"
    calls = []

    def start(self, session, company_id, user_id):
        self.calls.append(("start", session, company_id, user_id))
        if self.mode == "no_dataset":
            raise WorkflowDatasetUnavailableError("No workflow-ready dataset is available")
        if self.mode == "not_ready":
            raise WorkflowReadinessBlockedError(BusinessWorkflowReadiness(str(DATASET_ID), "BLOCKED", (CapabilityReadiness("backtest", "BLOCKED", "INSUFFICIENT_HISTORY", "Geçmiş veri yetersiz.", 16, 12),)))
        return _execution(), self.mode == "duplicate"

    @classmethod
    def get_status(cls, session, company_id, execution_id):
        cls.calls.append(("status", session, company_id, execution_id))
        if cls.mode == "missing":
            raise WorkflowNotFoundError("Workflow execution was not found")
        return _execution()

    @classmethod
    def get_result(cls, session, company_id, execution_id):
        cls.calls.append(("result", session, company_id, execution_id))
        if cls.mode == "not_ready":
            raise WorkflowResultNotReadyError("Workflow result is not available before completion")
        if cls.mode == "missing":
            raise WorkflowNotFoundError("Workflow execution was not found")
        return _execution(state="completed", progress=100, completed_at=NOW), {"forecast": {"items": []}}


def _request(method, path, *, authenticated=True, json=None):
    app = FastAPI()
    app.include_router(workflow_api.router, prefix="/api/v2")
    db = object()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    if authenticated:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=USER_ID, company_id=COMPANY_ID)

    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path, json=json)

    with patch.object(workflow_api, "CanonicalBusinessWorkflowService", StubWorkflowService):
        return asyncio.run(send()), db


class CanonicalBusinessWorkflowApiTests(unittest.TestCase):
    def setUp(self):
        StubWorkflowService.mode = "ok"
        StubWorkflowService.calls = []

    def test_unauthenticated_start_is_denied(self):
        response, _ = _request("POST", "/api/v2/workflows/business", authenticated=False, json={})
        self.assertEqual(response.status_code, 401)

    def test_no_current_dataset_is_conflict(self):
        StubWorkflowService.mode = "no_dataset"
        response, _ = _request("POST", "/api/v2/workflows/business", json={})
        self.assertEqual(response.status_code, 409)

    def test_known_mandatory_readiness_block_is_structured(self):
        StubWorkflowService.mode = "not_ready"
        response, _ = _request("POST", "/api/v2/workflows/business", json={})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "BUSINESS_WORKFLOW_NOT_READY")
        self.assertEqual(response.json()["detail"]["readiness"]["capabilities"][0]["reason_code"], "INSUFFICIENT_HISTORY")

    def test_ready_dataset_start_is_tenant_scoped(self):
        response, db = _request("POST", "/api/v2/workflows/business", json={})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["execution_id"], str(EXECUTION_ID))
        self.assertFalse(response.json()["duplicate"])
        self.assertEqual(StubWorkflowService.calls, [("start", db, COMPANY_ID, USER_ID)])

    def test_duplicate_active_returns_existing(self):
        StubWorkflowService.mode = "duplicate"
        response, _ = _request("POST", "/api/v2/workflows/business", json={})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["duplicate"])

    def test_client_cannot_supply_tenant_or_dataset(self):
        response, _ = _request("POST", "/api/v2/workflows/business", json={
            "company_id": str(uuid4()), "dataset_id": str(uuid4()),
        })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(StubWorkflowService.calls, [])

    def test_status_lookup_is_tenant_scoped(self):
        response, db = _request("GET", f"/api/v2/executions/{EXECUTION_ID}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "queued")
        self.assertEqual(StubWorkflowService.calls, [("status", db, COMPANY_ID, EXECUTION_ID)])

    def test_cross_tenant_or_missing_execution_is_not_disclosed(self):
        StubWorkflowService.mode = "missing"
        response, _ = _request("GET", f"/api/v2/executions/{EXECUTION_ID}")
        self.assertEqual(response.status_code, 404)

    def test_result_before_completion_is_conflict(self):
        StubWorkflowService.mode = "not_ready"
        response, _ = _request("GET", f"/api/v2/executions/{EXECUTION_ID}/result")
        self.assertEqual(response.status_code, 409)

    def test_completed_result_discovery(self):
        response, db = _request("GET", f"/api/v2/executions/{EXECUTION_ID}/result")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], {"forecast": {"items": []}})
        self.assertNotIn("company_id", response.json())
        self.assertEqual(StubWorkflowService.calls, [("result", db, COMPANY_ID, EXECUTION_ID)])

    def test_invalid_execution_id_is_rejected(self):
        response, _ = _request("GET", "/api/v2/executions/not-a-uuid")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
