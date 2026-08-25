"""Immutable, non-authoritative user opinion events for Decision Snapshots."""
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class DecisionFeedbackEvent(BaseModel):
    """Append-only feedback; it is audit evidence, never decision truth."""
    __tablename__ = "decision_feedback_events"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    decision_snapshot_id = Column(PG_UUID(as_uuid=True), ForeignKey("decision_snapshots.id", ondelete="RESTRICT"), nullable=False)
    candidate_ordinal = Column(Integer, nullable=True)
    candidate_type = Column(String(64), nullable=True)
    feedback_type = Column(String(32), nullable=False)
    comment = Column(String(1000), nullable=True)
    source_metadata = Column(JSONB, nullable=False, default=dict)
    supersedes_feedback_id = Column(PG_UUID(as_uuid=True), ForeignKey("decision_feedback_events.id", ondelete="RESTRICT"), nullable=True)
    feedback_fingerprint = Column(String(64), nullable=False)
    semantic_key = Column(String(128), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "company_id", "user_id", "decision_snapshot_id", "candidate_ordinal", "candidate_type",
            "feedback_type", "feedback_fingerprint", "supersedes_feedback_id",
            name="uq_decision_feedback_event_semantic_identity",
        ),
        UniqueConstraint(
            "company_id", "semantic_key",
            name="uq_decision_feedback_company_semantic_key",
        ),
    )


@event.listens_for(DecisionFeedbackEvent, "before_update")
def _immutable_feedback(mapper, connection, target):
    raise ValueError("DecisionFeedbackEvent is immutable")
