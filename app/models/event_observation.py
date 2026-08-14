"""Canonical company-scoped event occurrences and auditable revision lineage."""
from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class EventObservation(BaseModel):
    __tablename__ = "event_observations"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    event_identity = Column(String(128), nullable=False)
    event_type = Column(String(64), nullable=False)
    source_occurrence_reference = Column(String(128), nullable=False)
    scope_type = Column(String(32), nullable=False)
    scope_value = Column(String(128), nullable=True)
    demand_type = Column(String(16), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_period = Column(String(8), nullable=True)
    end_period = Column(String(8), nullable=True)
    authority_type = Column(String(32), nullable=False)
    source_system = Column(String(32), nullable=False)
    public_reference_id = Column(String(128), nullable=True)
    provenance = Column(JSONB, nullable=False, default=dict)
    status = Column(String(16), nullable=False, default="ACTIVE")
    source_identity_fingerprint = Column(String(64), nullable=False)
    current_evidence_fingerprint = Column(String(64), nullable=False)
    current_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    current_accepted_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "source_identity_fingerprint", name="uq_event_observation_source"),
        CheckConstraint("scope_type IN ('MATERIAL', 'PRODUCT_GROUP', 'PRODUCT_CLASS', 'COMPANY')", name="ck_event_observation_scope"),
        CheckConstraint("(scope_type = 'COMPANY' AND scope_value IS NULL) OR (scope_type <> 'COMPANY' AND scope_value IS NOT NULL)", name="ck_event_observation_scope_value"),
        CheckConstraint("authority_type IN ('COMPANY_EXPLICIT', 'PUBLIC_REFERENCE')", name="ck_event_observation_authority"),
        CheckConstraint("status IN ('ACTIVE', 'CANCELLED')", name="ck_event_observation_status"),
        CheckConstraint("end_date >= start_date", name="ck_event_observation_dates"),
    )


class EventRevision(BaseModel):
    __tablename__ = "event_revisions"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    event_observation_id = Column(PG_UUID(as_uuid=True), ForeignKey("event_observations.id", ondelete="RESTRICT"), nullable=False)
    actor_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approval_status = Column(String(16), nullable=False, default="proposed")
    previous_snapshot = Column(JSONB, nullable=False)
    proposed_snapshot = Column(JSONB, nullable=False)
    previous_evidence_fingerprint = Column(String(64), nullable=False)
    proposed_evidence_fingerprint = Column(String(64), nullable=False)
    correction_fingerprint = Column(String(64), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "correction_fingerprint", name="uq_event_revision_correction"),
        CheckConstraint("approval_status IN ('proposed', 'accepted', 'rejected')", name="ck_event_revision_status"),
    )
