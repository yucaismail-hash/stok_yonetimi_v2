"""Immutable, queryable projection of persisted Forecast RuntimeResultReferences."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from app.models.base import BaseModel

_LEVELS = "'finished_good', 'semi_finished_good', 'raw_material'"
_TYPES = "'sales', 'shipment', 'order', 'consumption', 'other'"

class ForecastVintage(BaseModel):
    __tablename__ = 'forecast_vintages'
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False)
    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey('runtime_executions.execution_id', ondelete='RESTRICT'), nullable=False)
    runtime_result_reference_id = Column(PG_UUID(as_uuid=True), ForeignKey('runtime_result_references.id', ondelete='RESTRICT'), nullable=False, unique=True)
    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey('datasets.id', ondelete='RESTRICT'), nullable=False)
    dataset_version_id = Column(PG_UUID(as_uuid=True), ForeignKey('dataset_versions.id', ondelete='SET NULL'), nullable=True)
    forecast_available_at = Column(DateTime(timezone=True), nullable=False)
    forecast_origin_period = Column(String(8), nullable=False)
    input_cutoff_period = Column(String(8), nullable=False)
    demand_type = Column(String(16), nullable=False)
    learning_score_at_run = Column(Numeric(8, 3), nullable=True)
    learning_score_version = Column(String(32), nullable=True)
    learning_score_breakdown = Column(JSONB, nullable=True)
    learning_score_observed_at = Column(DateTime(timezone=True), nullable=True)
    result_version = Column(String(32), nullable=False)
    contract_version = Column(String(32), nullable=False)
    __table_args__ = (CheckConstraint("forecast_origin_period ~ '^[0-9]{4}-W[0-9]{2}$'", name='ck_vintage_origin_period'), CheckConstraint("input_cutoff_period ~ '^[0-9]{4}-W[0-9]{2}$'", name='ck_vintage_cutoff_period'), CheckConstraint(f"demand_type IN ({_TYPES})", name='ck_vintage_demand_type'))

class ForecastVintagePoint(BaseModel):
    __tablename__ = 'forecast_vintage_points'
    forecast_vintage_id = Column(PG_UUID(as_uuid=True), ForeignKey('forecast_vintages.id', ondelete='RESTRICT'), nullable=False)
    material_code = Column(String(128), nullable=False)
    target_period = Column(String(8), nullable=False)
    forecast_value = Column(Numeric(18, 4), nullable=False)
    lower_interval = Column(Numeric(18, 4), nullable=True)
    upper_interval = Column(Numeric(18, 4), nullable=True)
    model_used = Column(String(128), nullable=True)
    selection_metadata = Column(JSONB, nullable=True)
    product_level = Column(String(32), nullable=False)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    horizon_index = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint('forecast_vintage_id','material_code','target_period',name='uq_vintage_point_target'), CheckConstraint("target_period ~ '^[0-9]{4}-W[0-9]{2}$'", name='ck_vintage_point_period'), CheckConstraint(f"product_level IN ({_LEVELS})", name='ck_vintage_point_level'), CheckConstraint('horizon_index >= 1', name='ck_vintage_point_horizon'))
