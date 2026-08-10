"""Canonical accepted weekly actuals and their append-only revision evidence."""
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel


_PRODUCT_LEVELS = "'finished_good', 'semi_finished_good', 'raw_material'"
_DEMAND_TYPES = "'sales', 'shipment', 'order', 'consumption', 'other'"
_REVISION_TYPES = "'new', 'correction'"
_APPROVAL_STATES = "'accepted', 'proposed', 'rejected'"


class ActualWeeklyObservation(BaseModel):
    __tablename__ = "actual_weekly_observations"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    period = Column(String(8), nullable=False)
    demand_type = Column(String(16), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    product_level = Column(String(32), nullable=False)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    source_dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False)
    source_dataset_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("company_id", "material_code", "period", "demand_type", name="uq_actual_weekly_identity"),
        CheckConstraint("period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_actual_weekly_period"),
        CheckConstraint(f"product_level IN ({_PRODUCT_LEVELS})", name="ck_actual_weekly_product_level"),
        CheckConstraint(f"demand_type IN ({_DEMAND_TYPES})", name="ck_actual_weekly_demand_type"),
    )


class ActualWeeklyRevision(BaseModel):
    __tablename__ = "actual_weekly_revisions"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    observation_id = Column(PG_UUID(as_uuid=True), ForeignKey("actual_weekly_observations.id", ondelete="RESTRICT"), nullable=True)
    material_code = Column(String(128), nullable=False)
    period = Column(String(8), nullable=False)
    demand_type = Column(String(16), nullable=False)
    previous_quantity = Column(Numeric(18, 4), nullable=True)
    proposed_quantity = Column(Numeric(18, 4), nullable=False)
    change_type = Column(String(16), nullable=False)
    approval_status = Column(String(16), nullable=False)
    product_level = Column(String(32), nullable=False)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    source_dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False)
    source_dataset_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True)
    actor_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_actual_revision_period"),
        CheckConstraint(f"demand_type IN ({_DEMAND_TYPES})", name="ck_actual_revision_demand_type"),
        CheckConstraint(f"product_level IN ({_PRODUCT_LEVELS})", name="ck_actual_revision_product_level"),
        CheckConstraint(f"change_type IN ({_REVISION_TYPES})", name="ck_actual_revision_type"),
        CheckConstraint(f"approval_status IN ({_APPROVAL_STATES})", name="ck_actual_revision_status"),
    )
