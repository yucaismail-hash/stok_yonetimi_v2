"""Durable, company-scoped intent to retrain one eligible Challenger scope."""

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class RetrainingJob(BaseModel):
    __tablename__ = "retraining_jobs"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    runtime_execution_id = Column(PG_UUID(as_uuid=True), nullable=True)
    state = Column(String(32), nullable=False, default="pending")
    model_artifact_id = Column(PG_UUID(as_uuid=True), ForeignKey("model_artifacts.id", ondelete="RESTRICT"), nullable=True)
    failure_code = Column(String(128), nullable=True)
    failure_reason = Column(String(512), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # B4 scheduling-control evidence.  Candidate identity remains the B1
    # fingerprint; these fields only explain when a candidate may execute.
    cooldown_policy_version = Column(String(32), nullable=True)
    cooldown_decision_at = Column(DateTime(timezone=True), nullable=True)
    cooldown_until = Column(DateTime(timezone=True), nullable=True)
    cooldown_reason_code = Column(String(128), nullable=True)
    priority_policy_version = Column(String(32), nullable=True)
    priority_score = Column(Numeric(18, 6), nullable=True)
    priority_calculated_at = Column(DateTime(timezone=True), nullable=True)
    admission_policy_version = Column(String(32), nullable=True)
    admission_result = Column(String(64), nullable=True)
    admission_reason_code = Column(String(128), nullable=True)
    admission_decided_at = Column(DateTime(timezone=True), nullable=True)

    eligibility_tier = Column(String(64), nullable=False)
    eligibility_action = Column(String(64), nullable=False)
    eligibility_contract_version = Column(String(32), nullable=False)
    eligibility_reason_codes = Column(JSONB, nullable=False)
    performance_drift = Column(Boolean, nullable=False)
    demand_drift = Column(Boolean, nullable=False)
    sample_count = Column(Integer, nullable=False)
    evaluated_period_count = Column(Integer, nullable=False)
    evaluation_start_period = Column(String(8), nullable=False)
    evaluation_end_period = Column(String(8), nullable=False)
    latest_evaluation_id = Column(PG_UUID(as_uuid=True), ForeignKey("forecast_evaluations.id", ondelete="RESTRICT"), nullable=False)
    training_cutoff_period = Column(String(8), nullable=False)

    product_level = Column(String(32), nullable=False)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    current_wape = Column(Numeric(18, 10), nullable=True)
    baseline_wape = Column(Numeric(18, 10), nullable=True)
    mean_signed_error = Column(Numeric(18, 10), nullable=True)
    evaluation_evidence_fingerprint = Column(String(64), nullable=False)
    candidate_fingerprint = Column(String(64), nullable=False)
    eligibility_evidence = Column(JSONB, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ("runtime_execution_id", "company_id"),
            ("runtime_executions.execution_id", "runtime_executions.company_id"),
            ondelete="RESTRICT",
            name="fk_retraining_jobs_runtime_execution_company",
        ),
        UniqueConstraint("company_id", "candidate_fingerprint", name="uq_retraining_job_candidate"),
        UniqueConstraint("company_id", "runtime_execution_id", name="uq_retraining_job_runtime_execution"),
        CheckConstraint("state IN ('pending', 'queued', 'running', 'trained', 'not_trainable', 'failed')", name="ck_retraining_job_state"),
        CheckConstraint("sample_count >= 0", name="ck_retraining_job_sample_count"),
        CheckConstraint("evaluated_period_count >= 0", name="ck_retraining_job_period_count"),
        Index("ix_retraining_job_scope", "company_id", "material_code", "demand_type", "created_at"),
    )
