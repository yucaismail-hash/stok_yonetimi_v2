"""Public contracts for the canonical tenant-scoped Business Workflow API."""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


RuntimeStatus = Literal[
    "created", "queued", "running", "waiting", "retrying",
    "completed", "failed", "cancelled",
]


class BusinessWorkflowStartRequest(BaseModel):
    """The first workflow has no client-controlled tenant or dataset inputs."""

    model_config = ConfigDict(extra="forbid")


class CapabilityReadinessResponse(BaseModel):
    capability: str
    status: Literal["READY", "READY_WITH_EXCLUSIONS", "WARNING", "BLOCKED", "EXCLUDED", "OPTIONAL_UNAVAILABLE"]
    reason_code: Optional[str] = None
    message: Optional[str] = None
    required_weeks: Optional[int] = None
    available_weeks: Optional[int] = None
    blocked_by: Optional[str] = None


class BusinessWorkflowReadinessResponse(BaseModel):
    dataset_id: UUID
    status: Literal["READY", "READY_WITH_EXCLUSIONS", "BLOCKED"]
    capabilities: list[CapabilityReadinessResponse]
    materials: list[Dict[str, Any]] = []
    coverage: Optional[Dict[str, Any]] = None


class BusinessWorkflowStartResponse(BaseModel):
    execution_id: UUID
    status: RuntimeStatus
    created_at: datetime
    workflow_type: Literal["business_workflow"]
    dataset_id: UUID
    duplicate: bool


class BusinessWorkflowStatusResponse(BaseModel):
    execution_id: UUID
    status: RuntimeStatus
    progress: float
    current_stage: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    failure_summary: Optional[str]
    dataset_id: UUID
    workflow_type: Literal["business_workflow"]
    workflow_id: str


class BusinessWorkflowResultResponse(BaseModel):
    execution_id: UUID
    workflow_type: Literal["business_workflow"]
    dataset_id: UUID
    completed_at: datetime
    result: Dict[str, Any]
