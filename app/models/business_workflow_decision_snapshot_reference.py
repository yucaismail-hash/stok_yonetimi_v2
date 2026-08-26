"""Immutable execution-local provenance for post-analytics Decisions."""

from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import BaseModel


class BusinessWorkflowDecisionSnapshotReference(BaseModel):
    """Links one completed workflow scope to the exact immutable Snapshot used."""

    __tablename__ = "business_workflow_decision_snapshot_references"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    execution_id = Column(PG_UUID(as_uuid=True), nullable=False)
    decision_finalization_id = Column(PG_UUID(as_uuid=True), nullable=False)
    decision_snapshot_id = Column(PG_UUID(as_uuid=True), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    decision_context = Column(String(64), nullable=False)
    decision_cutoff_period = Column(String(8), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ("execution_id", "company_id"),
            ("runtime_executions.execution_id", "runtime_executions.company_id"),
            ondelete="RESTRICT",
            name="fk_bw_dsref_execution_company",
        ),
        ForeignKeyConstraint(
            ("decision_finalization_id", "execution_id", "company_id"),
            ("business_workflow_decision_finalizations.id", "business_workflow_decision_finalizations.execution_id", "business_workflow_decision_finalizations.company_id"),
            ondelete="RESTRICT",
            name="fk_bw_dsref_finalization_execution_company",
        ),
        ForeignKeyConstraint(
            ("decision_snapshot_id", "company_id"),
            ("decision_snapshots.id", "decision_snapshots.company_id"),
            ondelete="RESTRICT",
            name="fk_bw_dsref_snapshot_company",
        ),
        UniqueConstraint(
            "company_id", "execution_id", "material_code", "demand_type", "decision_context",
            name="uq_business_decision_snapshot_reference_execution_scope",
        ),
    )


@event.listens_for(BusinessWorkflowDecisionSnapshotReference, "before_update")
def _immutable_business_decision_snapshot_reference(mapper, connection, target):
    raise ValueError("BusinessWorkflowDecisionSnapshotReference is immutable")
