"""Durable, company-scoped ownership record for Learning Evidence refresh delivery."""
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class LearningRefreshDelivery(BaseModel):
    __tablename__ = "learning_refresh_deliveries"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    learning_evidence_id = Column(PG_UUID(as_uuid=True), ForeignKey("learning_evidence.id", ondelete="RESTRICT"), nullable=False)
    delivery_contract_version = Column(String(32), nullable=False)
    state = Column(String(16), nullable=False, default="pending")
    attempt_count = Column(Integer, nullable=False, default=0)
    worker_id = Column(String(128), nullable=True)
    claim_token = Column(PG_UUID(as_uuid=True), nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_outcome = Column(JSONB, nullable=True)
    failure_code = Column(String(128), nullable=True)
    failure_reason = Column(String(512), nullable=True)
    row_version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("company_id", "learning_evidence_id", "delivery_contract_version", name="uq_learning_refresh_delivery_identity"),
        CheckConstraint("state IN ('pending', 'processing', 'completed', 'failed')", name="ck_learning_refresh_delivery_state"),
        CheckConstraint("attempt_count >= 0", name="ck_learning_refresh_delivery_attempt_count"),
        CheckConstraint("row_version >= 1", name="ck_learning_refresh_delivery_row_version"),
        Index("ix_learning_refresh_delivery_claimable", "company_id", "state", "lease_expires_at"),
    )
