"""Immutable audit vintage of a canonical Decision envelope and policy result."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel


class DecisionSnapshot(BaseModel):
    __tablename__ = "decision_snapshots"
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    decision_context = Column(String(64), nullable=False)
    decision_cutoff_period = Column(String(8), nullable=False)
    decision_policy_version = Column(String(64), nullable=False)
    confidence_policy_version = Column(String(64), nullable=False)
    decision_evidence_fingerprint = Column(String(64), nullable=False)
    decision_policy_fingerprint = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    agreement_status = Column(String(32), nullable=False)
    confidence = Column(Numeric(18, 10), nullable=False)
    supporting_evidence = Column(JSONB, nullable=False, default=list)
    conflicting_evidence = Column(JSONB, nullable=False, default=list)
    uncertainty_codes = Column(JSONB, nullable=False, default=list)
    source_provenance = Column(JSONB, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint(
        "company_id", "material_code", "demand_type", "decision_context", "decision_cutoff_period",
        "decision_policy_version", "decision_evidence_fingerprint", "decision_policy_fingerprint",
        name="uq_decision_snapshot_semantic_identity"),)


class DecisionSnapshotCandidate(BaseModel):
    __tablename__ = "decision_snapshot_candidates"
    decision_snapshot_id = Column(PG_UUID(as_uuid=True), ForeignKey("decision_snapshots.id", ondelete="RESTRICT"), nullable=False)
    ordinal = Column(Integer, nullable=False)
    candidate_type = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)
    priority = Column(Integer, nullable=False)
    reason_codes = Column(JSONB, nullable=False, default=list)
    supporting_evidence = Column(JSONB, nullable=False, default=list)
    conflicting_evidence = Column(JSONB, nullable=False, default=list)
    confidence = Column(Numeric(18, 10), nullable=False)
    expected_impact_references = Column(JSONB, nullable=False, default=list)
    what_would_change_this = Column(JSONB, nullable=False, default=list)
    __table_args__ = (UniqueConstraint("decision_snapshot_id", "ordinal", name="uq_decision_snapshot_candidate_ordinal"),)


@event.listens_for(DecisionSnapshot, "before_update")
@event.listens_for(DecisionSnapshotCandidate, "before_update")
def _immutable_snapshot(mapper, connection, target):
    raise ValueError("DecisionSnapshot is immutable")
