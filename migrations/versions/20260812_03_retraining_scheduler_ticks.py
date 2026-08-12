"""Add durable company-scoped retraining scanner scheduler ticks."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260812_03"
down_revision = "20260812_02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "retraining_scheduler_ticks",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tick_identity", sa.String(length=64), nullable=False),
        sa.Column("scheduler_policy_version", sa.String(length=32), nullable=False),
        sa.Column("scheduled_bucket_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cadence_seconds", sa.String(length=32), nullable=False),
        sa.Column("start_period", sa.String(length=8), nullable=False),
        sa.Column("end_period", sa.String(length=8), nullable=False),
        sa.Column("material_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("demand_type_scope", sa.String(length=16), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=128), nullable=True),
        sa.Column("failure_reason", sa.String(length=512), nullable=True),
        sa.Column("report_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("company_id", "tick_identity", name="uq_retraining_scheduler_tick_identity"),
    )
    op.create_index("ix_retraining_scheduler_tick_company_bucket", "retraining_scheduler_ticks", ["company_id", "scheduled_bucket_at"])


def downgrade():
    op.drop_index("ix_retraining_scheduler_tick_company_bucket", table_name="retraining_scheduler_ticks")
    op.drop_table("retraining_scheduler_ticks")
