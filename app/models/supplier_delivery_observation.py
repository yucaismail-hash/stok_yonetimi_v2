"""Canonical observed supplier-delivery facts and auditable correction lineage."""
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class SupplierDeliveryObservation(BaseModel):
    __tablename__ = "supplier_delivery_observations"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = Column(PG_UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    material_id = Column(PG_UUID(as_uuid=True), ForeignKey("user_materials.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    purchase_order_reference = Column(String(128), nullable=True)
    order_line_reference = Column(String(128), nullable=True)
    receipt_reference = Column(String(128), nullable=True)
    dispatch_date = Column(Date, nullable=True)
    promised_delivery_date = Column(Date, nullable=True)
    actual_receipt_date = Column(Date, nullable=False)
    ordered_quantity = Column(Numeric(18, 4), nullable=True)
    received_quantity = Column(Numeric(18, 4), nullable=True)
    observed_lead_time_days = Column(Integer, nullable=True)
    delivery_lateness_days = Column(Integer, nullable=True)
    on_time = Column(Boolean, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    source_system = Column(String(32), nullable=False)
    provenance = Column(JSONB, nullable=False, default=dict)
    source_identity_fingerprint = Column(String(64), nullable=False)
    current_evidence_fingerprint = Column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "source_identity_fingerprint", name="uq_supplier_delivery_observation_source"),
        CheckConstraint("ordered_quantity IS NULL OR ordered_quantity > 0", name="ck_supplier_delivery_ordered_quantity"),
        CheckConstraint("received_quantity IS NULL OR received_quantity >= 0", name="ck_supplier_delivery_received_quantity"),
        CheckConstraint("observed_lead_time_days IS NULL OR observed_lead_time_days >= 0", name="ck_supplier_delivery_lead_time"),
    )


class SupplierDeliveryObservationRevision(BaseModel):
    __tablename__ = "supplier_delivery_observation_revisions"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    observation_id = Column(PG_UUID(as_uuid=True), ForeignKey("supplier_delivery_observations.id", ondelete="RESTRICT"), nullable=False)
    actor_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_type = Column(String(16), nullable=False, default="correction")
    approval_status = Column(String(16), nullable=False, default="proposed")
    previous_snapshot = Column(JSONB, nullable=False)
    proposed_snapshot = Column(JSONB, nullable=False)
    previous_evidence_fingerprint = Column(String(64), nullable=False)
    proposed_evidence_fingerprint = Column(String(64), nullable=False)
    correction_fingerprint = Column(String(64), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "correction_fingerprint", name="uq_supplier_delivery_correction"),
        CheckConstraint("change_type = 'correction'", name="ck_supplier_delivery_revision_type"),
        CheckConstraint("approval_status IN ('proposed', 'accepted', 'rejected')", name="ck_supplier_delivery_revision_status"),
    )
