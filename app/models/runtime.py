"""Canonical durable runtime persistence models (ADR-029 through ADR-032)."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database import Base
from uuid_extensions import uuid7


_EXECUTION_STATES = "'created', 'queued', 'running', 'waiting', 'retrying', 'completed', 'failed', 'cancelled'"
_TASK_STATES = "'pending', 'running', 'completed', 'failed', 'skipped', 'cancelled'"


class RuntimeExecution(Base):
    __tablename__ = "runtime_executions"

    execution_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False)
    workflow_id = Column(String(128), nullable=False)
    objective_type = Column(String(64), nullable=True)
    analysis_type = Column(String(64), nullable=True)
    state = Column(String(32), nullable=False, server_default=text("'created'"))
    current_stage = Column(String(64), nullable=True)
    progress = Column(Numeric(5, 2), nullable=False, server_default=text("0"))
    idempotency_key = Column(String(128), nullable=True)
    row_version = Column(Integer, nullable=False, server_default=text("1"))
    request_id = Column(String(128), nullable=True)
    trace_id = Column(String(128), nullable=True)
    correlation_id = Column(String(128), nullable=True)
    contract_version = Column(String(32), nullable=False, server_default=text("'1.0.0'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    queued_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_requested = Column(Boolean, nullable=False, server_default=text("false"))
    terminal_error = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    tasks = relationship("RuntimeTask", back_populates="execution", passive_deletes=True)
    checkpoints = relationship("RuntimeCheckpoint", back_populates="execution", passive_deletes=True)
    result_references = relationship("RuntimeResultReference", back_populates="execution", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("execution_id", "company_id", name="uq_runtime_executions_execution_company"),
        CheckConstraint("(objective_type IS NULL) <> (analysis_type IS NULL)", name="ck_runtime_executions_intent_xor"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_runtime_executions_progress_range"),
        CheckConstraint("row_version >= 1", name="ck_runtime_executions_row_version"),
        CheckConstraint(f"state IN ({_EXECUTION_STATES})", name="ck_runtime_executions_state"),
        Index("ix_runtime_executions_company_created", "company_id", "created_at"),
        Index("ix_runtime_executions_company_state", "company_id", "state"),
        Index("ix_runtime_executions_workflow_id", "workflow_id"),
        Index("uq_runtime_executions_company_idempotency", "company_id", "idempotency_key", unique=True, postgresql_where=text("idempotency_key IS NOT NULL")),
        Index("ix_runtime_executions_active", "company_id", "state", "created_at", postgresql_where=text("state IN ('created', 'queued', 'running', 'waiting', 'retrying')")),
        Index("uq_runtime_executions_one_active_business_workflow", "company_id", unique=True, postgresql_where=text("analysis_type = 'business_workflow' AND state IN ('created', 'queued', 'running', 'waiting', 'retrying')")),
    )


class RuntimeTask(Base):
    __tablename__ = "runtime_tasks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7)
    execution_id = Column(PG_UUID(as_uuid=True), nullable=False)
    company_id = Column(PG_UUID(as_uuid=True), nullable=False)
    workflow_id = Column(String(128), nullable=False)
    task_id = Column(String(128), nullable=False)
    capability = Column(String(64), nullable=False)
    task_order = Column(Integer, nullable=False)
    required = Column(Boolean, nullable=False)
    skippable = Column(Boolean, nullable=False)
    dependencies = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    state = Column(String(32), nullable=False, server_default=text("'pending'"))
    current_attempt = Column(Integer, nullable=False, server_default=text("0"))
    max_attempts = Column(Integer, nullable=False, server_default=text("1"))
    retryable = Column(Boolean, nullable=False, server_default=text("false"))
    timeout_seconds = Column(Integer, nullable=True)
    assigned_worker_id = Column(String(128), nullable=True)
    lease_token = Column(PG_UUID(as_uuid=True), nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    error_summary = Column(JSONB, nullable=True)
    metrics = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    row_version = Column(Integer, nullable=False, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    queued_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("RuntimeExecution", back_populates="tasks")
    attempts = relationship("RuntimeTaskAttempt", back_populates="task", passive_deletes=True)
    checkpoints = relationship("RuntimeCheckpoint", back_populates="task", passive_deletes=True)
    result_references = relationship("RuntimeResultReference", back_populates="task", passive_deletes=True)

    __table_args__ = (
        ForeignKeyConstraint(("execution_id", "company_id"), ("runtime_executions.execution_id", "runtime_executions.company_id"), ondelete="CASCADE", name="fk_runtime_tasks_execution_company"),
        UniqueConstraint("execution_id", "task_id", name="uq_runtime_tasks_execution_task"),
        UniqueConstraint("id", "execution_id", "company_id", name="uq_runtime_tasks_id_execution_company"),
        CheckConstraint("task_order >= 0", name="ck_runtime_tasks_order"),
        CheckConstraint("current_attempt >= 0", name="ck_runtime_tasks_current_attempt"),
        CheckConstraint("max_attempts >= 1", name="ck_runtime_tasks_max_attempts"),
        CheckConstraint("current_attempt <= max_attempts", name="ck_runtime_tasks_attempt_range"),
        CheckConstraint("timeout_seconds IS NULL OR timeout_seconds > 0", name="ck_runtime_tasks_timeout"),
        CheckConstraint("row_version >= 1", name="ck_runtime_tasks_row_version"),
        CheckConstraint(f"state IN ({_TASK_STATES})", name="ck_runtime_tasks_state"),
        Index("ix_runtime_tasks_execution_order", "execution_id", "task_order"),
        Index("ix_runtime_tasks_execution_state", "execution_id", "state"),
        Index("ix_runtime_tasks_claimable_lease", "state", "lease_expires_at", postgresql_where=text("state IN ('pending', 'running')")),
        Index("ix_runtime_tasks_worker_heartbeat", "assigned_worker_id", "heartbeat_at"),
    )


class RuntimeTaskAttempt(Base):
    __tablename__ = "runtime_task_attempts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7)
    company_id = Column(PG_UUID(as_uuid=True), nullable=False)
    execution_id = Column(PG_UUID(as_uuid=True), nullable=False)
    runtime_task_id = Column(PG_UUID(as_uuid=True), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    worker_id = Column(String(128), nullable=True)
    lease_token = Column(PG_UUID(as_uuid=True), nullable=True)
    state = Column(String(32), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Numeric(14, 3), nullable=True)
    error = Column(JSONB, nullable=True)
    retryable = Column(Boolean, nullable=False, server_default=text("false"))
    metrics = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    task = relationship("RuntimeTask", back_populates="attempts")
    result_references = relationship("RuntimeResultReference", back_populates="attempt", passive_deletes=True)

    __table_args__ = (
        ForeignKeyConstraint(("runtime_task_id", "execution_id", "company_id"), ("runtime_tasks.id", "runtime_tasks.execution_id", "runtime_tasks.company_id"), ondelete="CASCADE", name="fk_runtime_attempts_task_execution_company"),
        UniqueConstraint("runtime_task_id", "attempt_number", name="uq_runtime_attempts_task_number"),
        CheckConstraint("attempt_number >= 1", name="ck_runtime_attempts_number"),
        CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="ck_runtime_attempts_duration"),
        CheckConstraint("completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at", name="ck_runtime_attempts_time_order"),
        CheckConstraint(f"state IN ({_TASK_STATES})", name="ck_runtime_attempts_state"),
        Index("ix_runtime_attempts_execution", "execution_id"),
        Index("ix_runtime_attempts_worker_created", "worker_id", "created_at"),
    )


class RuntimeCheckpoint(Base):
    __tablename__ = "runtime_checkpoints"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7)
    company_id = Column(PG_UUID(as_uuid=True), nullable=False)
    execution_id = Column(PG_UUID(as_uuid=True), nullable=False)
    runtime_task_id = Column(PG_UUID(as_uuid=True), ForeignKey("runtime_tasks.id", ondelete="SET NULL"), nullable=True)
    checkpoint_version = Column(Integer, nullable=False)
    state = Column(String(32), nullable=False)
    stage = Column(String(64), nullable=True)
    completed_task_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    current_task_id = Column(String(128), nullable=True)
    retry_counters = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    result_references = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    recovery_metadata = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    execution = relationship("RuntimeExecution", back_populates="checkpoints")
    task = relationship("RuntimeTask", back_populates="checkpoints")

    __table_args__ = (
        ForeignKeyConstraint(("execution_id", "company_id"), ("runtime_executions.execution_id", "runtime_executions.company_id"), ondelete="CASCADE", name="fk_runtime_checkpoints_execution_company"),
        UniqueConstraint("execution_id", "checkpoint_version", name="uq_runtime_checkpoints_execution_version"),
        CheckConstraint("checkpoint_version >= 1", name="ck_runtime_checkpoints_version"),
        CheckConstraint(f"state IN ({_EXECUTION_STATES})", name="ck_runtime_checkpoints_state"),
    )


class RuntimeResultReference(Base):
    __tablename__ = "runtime_result_references"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7)
    company_id = Column(PG_UUID(as_uuid=True), nullable=False)
    execution_id = Column(PG_UUID(as_uuid=True), nullable=False)
    runtime_task_id = Column(PG_UUID(as_uuid=True), ForeignKey("runtime_tasks.id", ondelete="SET NULL"), nullable=True)
    runtime_attempt_id = Column(PG_UUID(as_uuid=True), ForeignKey("runtime_task_attempts.id", ondelete="SET NULL"), nullable=True)
    result_type = Column(String(64), nullable=False)
    result_version = Column(String(32), nullable=False)
    contract_version = Column(String(32), nullable=False)
    storage_kind = Column(String(32), nullable=False)
    inline_result = Column(JSONB, nullable=True)
    location = Column(Text, nullable=True)
    checksum = Column(String(128), nullable=True)
    byte_size = Column(BigInteger, nullable=True)
    validation_status = Column(String(32), nullable=False)
    compression_metadata = Column(JSONB, nullable=True)
    encryption_metadata = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    execution = relationship("RuntimeExecution", back_populates="result_references")
    task = relationship("RuntimeTask", back_populates="result_references")
    attempt = relationship("RuntimeTaskAttempt", back_populates="result_references")

    __table_args__ = (
        ForeignKeyConstraint(("execution_id", "company_id"), ("runtime_executions.execution_id", "runtime_executions.company_id"), ondelete="CASCADE", name="fk_runtime_results_execution_company"),
        CheckConstraint("(inline_result IS NULL) <> (location IS NULL)", name="ck_runtime_results_storage_xor"),
        CheckConstraint("(storage_kind = 'inline_jsonb' AND inline_result IS NOT NULL AND location IS NULL) OR (storage_kind = 'external_reference' AND location IS NOT NULL AND inline_result IS NULL)", name="ck_runtime_results_storage_kind"),
        CheckConstraint("storage_kind IN ('inline_jsonb', 'external_reference')", name="ck_runtime_results_storage_kind_value"),
        CheckConstraint("validation_status IN ('validated', 'invalid')", name="ck_runtime_results_validation_status"),
        CheckConstraint("byte_size IS NULL OR byte_size >= 0", name="ck_runtime_results_byte_size"),
        Index("ix_runtime_results_execution", "execution_id"),
        Index("ix_runtime_results_task", "runtime_task_id"),
        Index("uq_runtime_results_execution_scope", "execution_id", "result_type", "result_version", unique=True, postgresql_where=text("runtime_task_id IS NULL")),
        Index("uq_runtime_results_task_scope", "execution_id", "runtime_task_id", "result_type", "result_version", unique=True, postgresql_where=text("runtime_task_id IS NOT NULL")),
    )
