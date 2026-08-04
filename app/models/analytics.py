# app/models/analytics.py
"""
Analytics models - Forecast, Safety Stock, Supplier, Simulation, Backtest results.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB  # ✅ JSONB import et
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("execution_results.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    sku_code = Column(String, nullable=False)
    model_used = Column(String, nullable=False)
    
    # ✅ JSON -> JSONB
    forecast_data = Column(JSONB, nullable=False)
    confidence_intervals = Column(JSONB, nullable=True)

    mae = Column(Float, nullable=True)
    mse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    r2_score = Column(Float, nullable=True)

    pattern_type = Column(String, nullable=True)
    seasonality_periods = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("ExecutionResult")


class SafetyStockResult(Base):
    __tablename__ = "safety_stock_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("execution_results.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    sku_code = Column(String, nullable=False)

    safety_stock = Column(Float, nullable=False)
    service_level = Column(Float, nullable=False)
    demand_variability = Column(Float, nullable=True)
    lead_time_variability = Column(Float, nullable=True)

    reorder_point = Column(Float, nullable=True)
    current_stock = Column(Float, nullable=True)
    stock_status = Column(String, nullable=True)

    safety_factor = Column(Float, nullable=True)
    lead_time_weeks = Column(Integer, nullable=True)
    forecast_horizon = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("ExecutionResult")


class SupplierResult(Base):
    __tablename__ = "supplier_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("execution_results.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    sku_code = Column(String, nullable=False)

    risk_score = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=False)
    cost_score = Column(Float, nullable=True)
    delivery_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)

    lt_mean = Column(Float, nullable=True)
    lt_std = Column(Float, nullable=True)
    lt_forecast = Column(Float, nullable=True)

    recommendation = Column(String, nullable=True)
    recommendation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("ExecutionResult")
    supplier = relationship("Supplier")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("execution_results.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    sku_code = Column(String, nullable=False)
    model_used = Column(String, nullable=False)

    # ✅ JSON -> JSONB
    actual_values = Column(JSONB, nullable=False)
    predicted_values = Column(JSONB, nullable=False)
    errors = Column(JSONB, nullable=True)

    mae = Column(Float, nullable=True)
    mse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)

    test_period_start = Column(DateTime(timezone=True), nullable=True)
    test_period_end = Column(DateTime(timezone=True), nullable=True)
    test_period_count = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("ExecutionResult")


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("execution_results.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    sku_code = Column(String, nullable=False)

    num_simulations = Column(Integer, nullable=False)
    confidence_level = Column(Float, default=0.95)

    # ✅ JSON -> JSONB
    simulation_data = Column(JSONB, nullable=False)
    percentiles = Column(JSONB, nullable=False)

    mean = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)

    value_at_risk = Column(Float, nullable=True)
    expected_shortfall = Column(Float, nullable=True)
    probability_of_stockout = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("ExecutionResult")