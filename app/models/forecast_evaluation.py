"""Durable current Forecast-to-Actual evaluation evidence."""
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel


_LEVELS = "'finished_good', 'semi_finished_good', 'raw_material'"
_TYPES = "'sales', 'shipment', 'order', 'consumption', 'other'"


class ForecastEvaluation(BaseModel):
    __tablename__ = "forecast_evaluations"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    demand_type = Column(String(16), nullable=False)
    start_period = Column(String(8), nullable=False)
    end_period = Column(String(8), nullable=False)
    metric_contract_version = Column(String(32), nullable=False)
    evaluated_point_count = Column(Integer, nullable=False, default=0)
    wape = Column(Numeric(18, 8), nullable=True)
    wape_unavailable_reason = Column(String(64), nullable=True)
    forecast_accuracy = Column(Numeric(18, 8), nullable=True)
    total_signed_error = Column(Numeric(18, 4), nullable=False, default=0)
    mean_signed_error = Column(Numeric(18, 8), nullable=True)
    mae = Column(Numeric(18, 8), nullable=True)
    rmse = Column(Numeric(18, 8), nullable=True)
    smape = Column(Numeric(18, 8), nullable=True)
    recalculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("company_id", "demand_type", "start_period", "end_period", "metric_contract_version", name="uq_forecast_evaluation_identity"),
        CheckConstraint("start_period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_evaluation_start_period"),
        CheckConstraint("end_period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_evaluation_end_period"),
        CheckConstraint(f"demand_type IN ({_TYPES})", name="ck_evaluation_demand_type"),
        CheckConstraint("evaluated_point_count >= 0", name="ck_evaluation_point_count"),
    )


class ForecastEvaluationPoint(BaseModel):
    __tablename__ = "forecast_evaluation_points"

    evaluation_id = Column(PG_UUID(as_uuid=True), ForeignKey("forecast_evaluations.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    target_period = Column(String(8), nullable=False)
    actual_observation_id = Column(PG_UUID(as_uuid=True), ForeignKey("actual_weekly_observations.id", ondelete="RESTRICT"), nullable=False)
    actual_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("actual_weekly_revisions.id", ondelete="SET NULL"), nullable=True)
    accepted_actual_quantity = Column(Numeric(18, 4), nullable=False)
    forecast_vintage_id = Column(PG_UUID(as_uuid=True), ForeignKey("forecast_vintages.id", ondelete="RESTRICT"), nullable=False)
    forecast_vintage_point_id = Column(PG_UUID(as_uuid=True), ForeignKey("forecast_vintage_points.id", ondelete="RESTRICT"), nullable=False)
    runtime_result_reference_id = Column(PG_UUID(as_uuid=True), ForeignKey("runtime_result_references.id", ondelete="RESTRICT"), nullable=False)
    forecast_value = Column(Numeric(18, 4), nullable=False)
    forecast_available_at = Column(DateTime(timezone=True), nullable=False)
    input_cutoff_period = Column(String(8), nullable=False)
    product_level = Column(String(32), nullable=False)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    learning_score_at_run = Column(Numeric(8, 3), nullable=True)
    error = Column(Numeric(18, 4), nullable=False)
    absolute_error = Column(Numeric(18, 4), nullable=False)
    squared_error = Column(Numeric(28, 8), nullable=False)
    bias_contribution = Column(Numeric(18, 4), nullable=False)

    __table_args__ = (
        UniqueConstraint("evaluation_id", "material_code", "target_period", name="uq_evaluation_point_identity"),
        CheckConstraint("target_period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_evaluation_point_period"),
        CheckConstraint("input_cutoff_period ~ '^[0-9]{4}-W[0-9]{2}$'", name="ck_evaluation_point_cutoff"),
        CheckConstraint(f"product_level IN ({_LEVELS})", name="ck_evaluation_point_level"),
    )
