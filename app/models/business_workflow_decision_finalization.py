"""Durable advisory post-analytics Decision finalization lifecycle."""

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class BusinessWorkflowDecisionFinalization(BaseModel):
    """Mutable operational state; immutable Decision provenance remains separate."""

    __tablename__ = "business_workflow_decision_finalizations"

    company_id = Column(PG_UUID(as_uuid=True), nullable=False)
    execution_id = Column(PG_UUID(as_uuid=True), nullable=False)
    aggregate_result_reference_id = Column(PG_UUID(as_uuid=True), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    attempt_count = Column(Integer, nullable=False, default=0)
    row_version = Column(Integer, nullable=False, default=1)
    lease_token = Column(PG_UUID(as_uuid=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_material_codes = Column(JSONB, nullable=False, default=list)
    limitations = Column(JSONB, nullable=False, default=list)
    last_error = Column(JSONB, nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ("execution_id", "company_id"),
            ("runtime_executions.execution_id", "runtime_executions.company_id"),
            ondelete="RESTRICT",
            name="fk_business_decision_finalization_execution_company",
        ),
        ForeignKeyConstraint(
            ("aggregate_result_reference_id", "execution_id", "company_id"),
            ("runtime_result_references.id", "runtime_result_references.execution_id", "runtime_result_references.company_id"),
            ondelete="RESTRICT",
            name="fk_business_decision_finalization_aggregate_execution_company",
        ),
        UniqueConstraint("company_id", "execution_id", name="uq_business_decision_finalization_execution"),
        CheckConstraint("status IN ('pending', 'running', 'succeeded', 'partially_succeeded', 'failed')", name="ck_business_decision_finalization_status"),
        CheckConstraint("attempt_count >= 0", name="ck_business_decision_finalization_attempt_count"),
        CheckConstraint("row_version >= 1", name="ck_business_decision_finalization_row_version"),
        CheckConstraint("status = 'running' OR (lease_token IS NULL AND lease_expires_at IS NULL)", name="ck_business_decision_finalization_terminal_lease_clear"),
        CheckConstraint("status <> 'running' OR (lease_token IS NOT NULL AND lease_expires_at IS NOT NULL)", name="ck_business_decision_finalization_running_lease"),
        Index("ix_business_decision_finalization_recovery", "company_id", "status", "lease_expires_at"),
    )
