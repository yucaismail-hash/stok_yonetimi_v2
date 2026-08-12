"""Add durable cooldown, priority, and resource-admission evidence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260812_02"
down_revision = "20260812_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("retraining_jobs", sa.Column("cooldown_policy_version", sa.String(length=32), nullable=True))
    op.add_column("retraining_jobs", sa.Column("cooldown_decision_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("retraining_jobs", sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("retraining_jobs", sa.Column("cooldown_reason_code", sa.String(length=128), nullable=True))
    op.add_column("retraining_jobs", sa.Column("priority_policy_version", sa.String(length=32), nullable=True))
    op.add_column("retraining_jobs", sa.Column("priority_score", sa.Numeric(precision=18, scale=6), nullable=True))
    op.add_column("retraining_jobs", sa.Column("priority_calculated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("retraining_jobs", sa.Column("admission_policy_version", sa.String(length=32), nullable=True))
    op.add_column("retraining_jobs", sa.Column("admission_result", sa.String(length=64), nullable=True))
    op.add_column("retraining_jobs", sa.Column("admission_reason_code", sa.String(length=128), nullable=True))
    op.add_column("retraining_jobs", sa.Column("admission_decided_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "retraining_resource_leases",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("retraining_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("retraining_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=False),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("release_reason_code", sa.String(length=128), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("uq_retraining_resource_active_job", "retraining_resource_leases", ["retraining_job_id"], unique=True,
                    postgresql_where=sa.text("active = true"))
    op.create_index("ix_retraining_resource_active_capacity", "retraining_resource_leases", ["active", "lease_expires_at"])
    op.create_index("ix_retraining_resource_company_active", "retraining_resource_leases", ["company_id", "active", "lease_expires_at"])


def downgrade():
    op.drop_index("ix_retraining_resource_company_active", table_name="retraining_resource_leases")
    op.drop_index("ix_retraining_resource_active_capacity", table_name="retraining_resource_leases")
    op.drop_index("uq_retraining_resource_active_job", table_name="retraining_resource_leases")
    op.drop_table("retraining_resource_leases")
    for column in ("admission_decided_at", "admission_reason_code", "admission_result", "admission_policy_version",
                   "priority_calculated_at", "priority_score", "priority_policy_version", "cooldown_reason_code",
                   "cooldown_until", "cooldown_decision_at", "cooldown_policy_version"):
        op.drop_column("retraining_jobs", column)
