"""Enforce one active Business Workflow per company."""

from alembic import op
import sqlalchemy as sa


revision = "20260810_05"
down_revision = "20260810_04"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_runtime_executions_one_active_business_workflow",
        "runtime_executions",
        ["company_id"],
        unique=True,
        postgresql_where=sa.text("analysis_type = 'business_workflow' AND state IN ('created', 'queued', 'running', 'waiting', 'retrying')"),
    )


def downgrade():
    op.drop_index("uq_runtime_executions_one_active_business_workflow", table_name="runtime_executions")
