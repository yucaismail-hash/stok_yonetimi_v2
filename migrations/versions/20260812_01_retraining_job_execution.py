"""Add explicit leased execution lifecycle to durable retraining jobs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260812_01"
down_revision = "20260811_03"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_retraining_job_initial_pending", "retraining_jobs", type_="check")
    op.add_column("retraining_jobs", sa.Column("model_artifact_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("retraining_jobs", sa.Column("failure_code", sa.String(length=128), nullable=True))
    op.add_column("retraining_jobs", sa.Column("failure_reason", sa.String(length=512), nullable=True))
    op.add_column("retraining_jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("retraining_jobs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_retraining_jobs_model_artifact", "retraining_jobs", "model_artifacts", ["model_artifact_id"], ["id"], ondelete="RESTRICT")
    op.create_unique_constraint("uq_retraining_job_runtime_execution", "retraining_jobs", ["company_id", "runtime_execution_id"])
    op.create_check_constraint("ck_retraining_job_state", "retraining_jobs", "state IN ('pending', 'queued', 'running', 'trained', 'not_trainable', 'failed')")


def downgrade():
    op.drop_constraint("ck_retraining_job_state", "retraining_jobs", type_="check")
    op.drop_constraint("uq_retraining_job_runtime_execution", "retraining_jobs", type_="unique")
    op.drop_constraint("fk_retraining_jobs_model_artifact", "retraining_jobs", type_="foreignkey")
    op.drop_column("retraining_jobs", "completed_at")
    op.drop_column("retraining_jobs", "started_at")
    op.drop_column("retraining_jobs", "failure_reason")
    op.drop_column("retraining_jobs", "failure_code")
    op.drop_column("retraining_jobs", "model_artifact_id")
    op.create_check_constraint("ck_retraining_job_initial_pending", "retraining_jobs", "state = 'pending'")
