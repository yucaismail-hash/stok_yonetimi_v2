"""Durable ownership and audit record for one company-scoped scanner tick."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class RetrainingSchedulerTick(BaseModel):
    __tablename__ = "retraining_scheduler_ticks"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    tick_identity = Column(String(64), nullable=False)
    scheduler_policy_version = Column(String(32), nullable=False)
    scheduled_bucket_at = Column(DateTime(timezone=True), nullable=False)
    cadence_seconds = Column(String(32), nullable=False)
    start_period = Column(String(8), nullable=False)
    end_period = Column(String(8), nullable=False)
    material_scope = Column(JSONB, nullable=True)
    demand_type_scope = Column(String(16), nullable=True)
    state = Column(String(32), nullable=False, default="running")
    owner_id = Column(String(128), nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(128), nullable=True)
    failure_reason = Column(String(512), nullable=True)
    report_summary = Column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "tick_identity", name="uq_retraining_scheduler_tick_identity"),
        Index("ix_retraining_scheduler_tick_company_bucket", "company_id", "scheduled_bucket_at"),
    )
