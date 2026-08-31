"""Immutable operational product inputs owned by one accepted DatasetVersion."""
from sqlalchemy import Column, ForeignKey, Numeric, String, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.models.base import BaseModel


class DatasetVersionProductInput(BaseModel):
    __tablename__ = "dataset_version_product_inputs"
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    dataset_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    product_name = Column(String(256), nullable=True)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    product_level = Column(String(32), nullable=False)
    initial_stock = Column(Numeric(18, 4), nullable=False)
    lead_time_days = Column(Numeric(18, 4), nullable=False)
    lot_size = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=True)
    holding_rate = Column(Numeric(18, 8), nullable=True)
    stockout_cost = Column(Numeric(18, 4), nullable=True)
    __table_args__ = (
        UniqueConstraint("dataset_version_id", "material_code", name="uq_dataset_version_product_input"),
        CheckConstraint("product_level IN ('finished_good','semi_finished_good','raw_material')", name="ck_dataset_version_product_input_level"),
        CheckConstraint("initial_stock >= 0 AND lead_time_days > 0 AND lot_size >= 0 AND unit_cost >= 0 AND holding_rate >= 0 AND stockout_cost >= 0", name="ck_dataset_version_product_input_nonnegative"),
        Index("ix_dataset_version_product_input_company_version_material", "company_id", "dataset_version_id", "material_code"),
    )
