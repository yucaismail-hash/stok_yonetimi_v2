# app/schemas/decision.py
"""
Decision Pydantic Schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DecisionRunRequest(BaseModel):
    """Decision run request."""
    objective_type: str = Field(..., description="Business objective type")
    dataset_id: int = Field(..., description="Dataset ID to use")
    params: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")
    language: Optional[str] = Field("Türkçe", description="Response language")


class DecisionRunResponse(BaseModel):
    """Decision run response."""
    workflow_id: str
    objective_type: str
    dataset_id: int
    status: str
    message: str
    status_url: Optional[str] = None


class DecisionTaskStatus(BaseModel):
    """Individual task status."""
    task_type: str
    status: str
    is_functional: bool
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class DecisionStatusResponse(BaseModel):
    """Decision status response."""
    workflow_id: str
    objective_type: str
    status: str
    progress: int
    current_stage: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    tasks: List[DecisionTaskStatus] = []
    result: Optional[Dict[str, Any]] = None
    ai_decision: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ObjectiveListItem(BaseModel):
    """Objective list item."""
    type: str
    name: str
    description: str
    steps: List[Dict[str, Any]]


class ObjectiveListResponse(BaseModel):
    """Objective list response."""
    total: int
    objectives: List[ObjectiveListItem]
    message: str