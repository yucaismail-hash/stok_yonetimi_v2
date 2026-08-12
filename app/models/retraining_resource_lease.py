"""PostgreSQL-backed global retraining-lane leases."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import BaseModel


class RetrainingResourceLease(BaseModel):
    __tablename__ = "retraining_resource_leases"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    retraining_job_id = Column(PG_UUID(as_uuid=True), ForeignKey("retraining_jobs.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String(128), nullable=False)
    lease_token = Column(PG_UUID(as_uuid=True), nullable=False, unique=True)
    claimed_at = Column(DateTime(timezone=True), nullable=False)
    heartbeat_at = Column(DateTime(timezone=True), nullable=False)
    lease_expires_at = Column(DateTime(timezone=True), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    release_reason_code = Column(String(128), nullable=True)

    __table_args__ = (
        Index("uq_retraining_resource_active_job", "retraining_job_id", unique=True,
              postgresql_where=text("active = true")),
        Index("ix_retraining_resource_active_capacity", "active", "lease_expires_at"),
        Index("ix_retraining_resource_company_active", "company_id", "active", "lease_expires_at"),
    )
