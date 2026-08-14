"""Mutable current projection of cutoff-safe, non-causal Event Association evidence."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel


class EventIntelligenceMemory(BaseModel):
    __tablename__ = "event_intelligence_memory"
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    event_identity = Column(String(128), nullable=False)
    event_type_snapshot = Column(String(64), nullable=True)
    product_level = Column(String(32), nullable=True)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    feature_schema_version = Column(String(32), nullable=False)
    baseline_policy_version = Column(String(32), nullable=False)
    lag_policy_version = Column(String(32), nullable=False)
    association_policy_version = Column(String(32), nullable=False)
    confidence_policy_version = Column(String(32), nullable=False)
    classification = Column(String(64), nullable=False)
    confidence = Column(Numeric(18, 10), nullable=False)
    occurrence_count = Column(Integer, nullable=False)
    included_occurrence_ids = Column(JSONB, nullable=False, default=list)
    included_revision_ids = Column(JSONB, nullable=False, default=list)
    cutoff_period = Column(String(8), nullable=False)
    baseline_method = Column(String(64), nullable=True)
    baseline_source_vintage_ids = Column(JSONB, nullable=False, default=list)
    baseline_source_periods = Column(JSONB, nullable=False, default=list)
    event_actual_mean = Column(Numeric(18, 8), nullable=True)
    baseline_mean = Column(Numeric(18, 8), nullable=True)
    absolute_effect = Column(Numeric(18, 8), nullable=True)
    relative_effect = Column(Numeric(18, 10), nullable=True)
    pre_event_mean = Column(Numeric(18, 8), nullable=True)
    post_event_mean = Column(Numeric(18, 8), nullable=True)
    pre_change = Column(Numeric(18, 8), nullable=True)
    post_decay = Column(Numeric(18, 8), nullable=True)
    strongest_lag_weeks = Column(Integer, nullable=True)
    strongest_lag_relative_effect = Column(Numeric(18, 10), nullable=True)
    mean_relative_effect = Column(Numeric(18, 10), nullable=True)
    median_relative_effect = Column(Numeric(18, 10), nullable=True)
    effect_dispersion = Column(Numeric(18, 10), nullable=True)
    direction_consistency = Column(Numeric(18, 10), nullable=True)
    overlap_confounded = Column(Boolean, nullable=False, default=False)
    confounded_occurrence_ids = Column(JSONB, nullable=False, default=list)
    source_actual_observation_ids = Column(JSONB, nullable=False, default=list)
    source_actual_revision_ids = Column(JSONB, nullable=False, default=list)
    source_fingerprint = Column(String(64), nullable=False)
    source_scope_metadata = Column(JSONB, nullable=False, default=dict)
    last_materialized_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    row_version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("company_id", "material_code", "demand_type", "event_identity", name="uq_event_intelligence_memory_scope"),
        Index("ix_event_intelligence_memory_company_scope", "company_id", "material_code", "demand_type", "event_identity"),
    )
