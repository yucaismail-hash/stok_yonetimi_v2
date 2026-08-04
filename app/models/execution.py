# app/models/execution.py
"""
Execution models - Analysis results and metrics.
Follows DOCUMENT 03 - Database Architecture Specification.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class AnalysisResult(BaseModel):
    """Tüm analiz sonuçları (Senkron + Async)"""
    __tablename__ = "analysis_results"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    upload_id = Column(String, nullable=True, index=True)
    result_type = Column(String, nullable=False, index=True)

    data = Column(JSONB, nullable=False)
    params = Column(JSONB, default={})

    task_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    message = Column(String, nullable=True)

    total_materials = Column(Integer, default=0)

    expires_at = Column(DateTime, nullable=True)

    ai_summary = Column(JSONB, nullable=True)
    ai_status = Column(String, nullable=True)
    ai_version = Column(String, nullable=True)
    ai_created_at = Column(DateTime, nullable=True)
    ai_prompt_version = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="results")
    company = relationship("Company", back_populates="execution_results")


class ExecutionResult(BaseModel):
    """Execution results - alias for AnalysisResult for compatibility."""
    __tablename__ = "execution_results"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    
    objective_type = Column(String, nullable=False)
    workflow_id = Column(String, nullable=False)
    task_id = Column(String, nullable=True)
    result_type = Column(String, nullable=False)
    result_data = Column(JSONB, nullable=False)
    params = Column(JSONB, nullable=True)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    message = Column(String(500), nullable=True)
    total_materials = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    ai_summary = Column(JSONB, nullable=True)
    ai_status = Column(String(50), nullable=True)
    ai_version = Column(String(50), nullable=True)
    ai_created_at = Column(DateTime(timezone=True), nullable=True)
    ai_prompt_version = Column(String(50), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    company = relationship("Company")

    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
    )


class ExecutionMetrics(BaseModel):
    __tablename__ = "execution_metrics"

    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("execution_results.id"), nullable=False, unique=True)
    total_duration_ms = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    ram_usage_mb = Column(Float, nullable=True)
    peak_ram_mb = Column(Float, nullable=True)
    algorithm_version = Column(String, nullable=True)
    worker_info = Column(String, nullable=True)
    total_api_calls = Column(Integer, default=0)
    total_token_cost = Column(Integer, default=0)

    __table_args__ = (
        CheckConstraint('total_duration_ms >= 0', name='check_duration_positive'),
        CheckConstraint('cpu_usage_percent >= 0', name='check_cpu_positive'),
        CheckConstraint('ram_usage_mb >= 0', name='check_ram_positive'),
    )


class ExecutionStageMetrics(BaseModel):
    __tablename__ = "execution_stage_metrics"

    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("execution_results.id"), nullable=False)
    stage_name = Column(String, nullable=False)
    duration_ms = Column(Float, nullable=True)
    record_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)


class ExecutionResourceMetrics(BaseModel):
    __tablename__ = "execution_resource_metrics"

    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("execution_results.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_value = Column(Float, nullable=False)
    unit = Column(String, default="percent")
    measured_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('resource_value >= 0', name='check_resource_positive'),
    )


class ExecutionCache(BaseModel):
    __tablename__ = "execution_cache"

    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    sku_code = Column(String, nullable=False)
    result_type = Column(String, nullable=False)
    result_data = Column(JSONB, nullable=False)
    result_hash = Column(String(64), nullable=False)
    algorithm_version = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_valid = Column(Boolean, default=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="cache_entries")