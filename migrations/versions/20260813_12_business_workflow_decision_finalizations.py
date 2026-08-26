"""Add durable advisory Decision finalization lifecycle for completed workflows."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260813_12"
down_revision = "20260813_11"
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL needs this referenced composite key to enforce aggregate
    # ownership without trusting application-supplied company/execution IDs.
    op.create_unique_constraint(
        "uq_runtime_results_id_execution_company",
        "runtime_result_references",
        ["id", "execution_id", "company_id"],
    )
    op.create_table(
        "business_workflow_decision_finalizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("is_deleted", sa.Boolean()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_result_reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("completed_material_codes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("limitations", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("last_error", postgresql.JSONB()),
        sa.Column("finalized_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(("execution_id", "company_id"), ("runtime_executions.execution_id", "runtime_executions.company_id"), ondelete="RESTRICT", name="fk_business_decision_finalization_execution_company"),
        sa.ForeignKeyConstraint(("aggregate_result_reference_id", "execution_id", "company_id"), ("runtime_result_references.id", "runtime_result_references.execution_id", "runtime_result_references.company_id"), ondelete="RESTRICT", name="fk_business_decision_finalization_aggregate_execution_company"),
        sa.UniqueConstraint("company_id", "execution_id", name="uq_business_decision_finalization_execution"),
        sa.CheckConstraint("status IN ('pending', 'running', 'succeeded', 'partially_succeeded', 'failed')", name="ck_business_decision_finalization_status"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_business_decision_finalization_attempt_count"),
        sa.CheckConstraint("row_version >= 1", name="ck_business_decision_finalization_row_version"),
        sa.CheckConstraint("status = 'running' OR (lease_token IS NULL AND lease_expires_at IS NULL)", name="ck_business_decision_finalization_terminal_lease_clear"),
        sa.CheckConstraint("status <> 'running' OR (lease_token IS NOT NULL AND lease_expires_at IS NOT NULL)", name="ck_business_decision_finalization_running_lease"),
    )
    op.create_index("ix_business_decision_finalization_recovery", "business_workflow_decision_finalizations", ["company_id", "status", "lease_expires_at"])


def downgrade():
    op.drop_index("ix_business_decision_finalization_recovery", table_name="business_workflow_decision_finalizations")
    op.drop_table("business_workflow_decision_finalizations")
    op.drop_constraint("uq_runtime_results_id_execution_company", "runtime_result_references", type_="unique")
