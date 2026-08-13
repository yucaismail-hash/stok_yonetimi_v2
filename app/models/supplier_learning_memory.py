"""Mutable current projection of canonical Supplier Learning calculations."""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel


class SupplierLearningMemory(BaseModel):
    __tablename__ = "supplier_learning_memory"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = Column(PG_UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    supplier_code = Column(String(128), nullable=False)
    supplier_name = Column(String(256), nullable=False)
    product_level = Column(String(32), nullable=True)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    supplier_learning_policy_version = Column(String(64), nullable=False)
    feature_version = Column(String(64), nullable=False)
    confidence_policy_version = Column(String(64), nullable=False)
    classification = Column(String(64), nullable=False)
    confidence = Column(Numeric(18, 10), nullable=False)
    sample_count = Column(Integer, nullable=False)
    lead_time_sample_count = Column(Integer, nullable=False)
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    cutoff_date = Column(Date, nullable=False)
    mean_observed_lead_time_days = Column(Numeric(18, 8), nullable=True)
    median_observed_lead_time_days = Column(Numeric(18, 8), nullable=True)
    std_observed_lead_time_days = Column(Numeric(18, 8), nullable=True)
    lead_time_coefficient_of_variation = Column(Numeric(18, 10), nullable=True)
    min_observed_lead_time_days = Column(Integer, nullable=True)
    max_observed_lead_time_days = Column(Integer, nullable=True)
    p50_observed_lead_time_days = Column(Numeric(18, 8), nullable=True)
    p90_observed_lead_time_days = Column(Numeric(18, 8), nullable=True)
    lead_time_percentile_spread_days = Column(Numeric(18, 8), nullable=True)
    promised_delivery_sample_count = Column(Integer, nullable=False)
    on_time_count = Column(Integer, nullable=False)
    late_count = Column(Integer, nullable=False)
    on_time_ratio = Column(Numeric(18, 10), nullable=True)
    late_ratio = Column(Numeric(18, 10), nullable=True)
    mean_lateness_days = Column(Numeric(18, 8), nullable=True)
    fulfillment_sample_count = Column(Integer, nullable=False)
    mean_fulfillment_ratio = Column(Numeric(18, 10), nullable=True)
    underfulfillment_count = Column(Integer, nullable=False)
    underfulfillment_ratio = Column(Numeric(18, 10), nullable=True)
    recent_window_size = Column(Integer, nullable=False)
    recent_deterioration_evaluated = Column(String(8), nullable=False)
    recent_lead_time_change_ratio = Column(Numeric(18, 10), nullable=True)
    recent_late_ratio_change = Column(Numeric(18, 10), nullable=True)
    recent_fulfillment_change_ratio = Column(Numeric(18, 10), nullable=True)
    recent_deterioration_dimensions = Column(JSONB, nullable=False, default=list)
    source_fingerprint = Column(String(64), nullable=False)
    source_observation_ids = Column(JSONB, nullable=False, default=list)
    accepted_revision_ids = Column(JSONB, nullable=False, default=list)
    last_materialized_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    row_version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("company_id", "supplier_id", "material_code", name="uq_supplier_learning_memory_scope"),
        Index("ix_supplier_learning_memory_company_scope", "company_id", "supplier_id", "material_code"),
    )
