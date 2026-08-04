# app/models/workflow.py
"""
Workflow models - Orchestration engine.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WorkflowExecution(Base):
    """DOCUMENT 01: Workflow orchestration execution."""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    # DOCUMENT 01: Business Objective
    objective_type = Column(String, nullable=False)  # reduce_stockout, optimize_inventory, etc.
    objective_params = Column(JSONB, nullable=True)

    # Workflow state
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    current_stage = Column(String, nullable=True)
    progress = Column(Integer, default=0)

    # DOCUMENT 01: Dependency management
    functional_dependencies = Column(JSONB, nullable=True)
    enrichment_dependencies = Column(JSONB, nullable=True)
    skipped_enrichments = Column(JSONB, nullable=True)

    # Results
    final_result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tasks = relationship("WorkflowTask", back_populates="workflow")


class WorkflowTask(Base):
    """Individual task within a workflow."""
    __tablename__ = "workflow_tasks"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False)

    task_type = Column(String, nullable=False)  # forecast, safety_stock, simulation, backtest, supplier
    task_order = Column(Integer, nullable=False)

    # Dependency
    depends_on = Column(JSONB, nullable=True)  # List of task types this depends on
    is_functional = Column(Boolean, default=True)  # True=Functional, False=Enrichment

    # Execution
    status = Column(String(20), default="pending")
    result_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metrics
    duration_ms = Column(Float, nullable=True)
    record_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workflow = relationship("WorkflowExecution", back_populates="tasks")