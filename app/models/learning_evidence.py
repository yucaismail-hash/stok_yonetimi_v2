"""Immutable, source-derived evidence for future Company and Pattern Learning."""

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, String, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel


class LearningEvidence(BaseModel):
    __tablename__ = "learning_evidence"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    event_type = Column(String(32), nullable=False)
    material_code = Column(String(128), nullable=True)
    demand_type = Column(String(16), nullable=True)
    source_entity_type = Column(String(64), nullable=False)
    source_entity_id = Column(PG_UUID(as_uuid=True), nullable=False)
    source_revision_identity = Column(String(256), nullable=False)
    affected_start_period = Column(String(8), nullable=True)
    affected_end_period = Column(String(8), nullable=True)
    evidence_fingerprint = Column(String(64), nullable=False)
    contract_version = Column(String(32), nullable=False)
    payload_version = Column(String(32), nullable=False)
    evidence_payload = Column(JSONB, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    supersedes_evidence_id = Column(PG_UUID(as_uuid=True), ForeignKey("learning_evidence.id", ondelete="RESTRICT"), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "evidence_fingerprint", name="uq_learning_evidence_company_fingerprint"),
        CheckConstraint("event_type IN ('ACTUAL_ACCEPTED', 'ACTUAL_CORRECTED', 'FORECAST_EVALUATED', 'CHAMPION_PROMOTED', 'CHAMPION_ROLLED_BACK', 'RETRAINING_COMPLETED', 'SUPPLIER_DELIVERY_OBSERVED', 'SUPPLIER_DELIVERY_CORRECTED', 'EVENT_OBSERVED', 'EVENT_CORRECTED', 'EVENT_CANCELLED')", name="ck_learning_evidence_event_type"),
        CheckConstraint("affected_start_period IS NULL OR affected_start_period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_learning_evidence_start_period"),
        CheckConstraint("affected_end_period IS NULL OR affected_end_period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_learning_evidence_end_period"),
        Index("ix_learning_evidence_company_scope", "company_id", "material_code", "demand_type", "recorded_at"),
    )


def _immutable(mapper, connection, target):
    raise ValueError("LearningEvidence is immutable")


event.listen(LearningEvidence, "before_update", _immutable)
