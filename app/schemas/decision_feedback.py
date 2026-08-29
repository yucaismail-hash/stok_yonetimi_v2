"""HTTP contracts for append-only feedback on immutable Decision Snapshots."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DecisionFeedbackRequest(BaseModel):
    feedback_type: Literal["HELPFUL", "NOT_HELPFUL"]
    candidate_ordinal: int | None = None
    candidate_type: str | None = None
    comment: str | None = Field(default=None, max_length=1000)
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    supersedes_feedback_id: UUID | None = None


class DecisionFeedbackResponse(BaseModel):
    status: Literal["CREATED", "ALREADY_EXISTS"]
    feedback_id: UUID
