"""Add immutable execution-to-Decision Snapshot provenance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260813_13"
down_revision = "20260813_12"
branch_labels = None
depends_on = None


def upgrade():
    # Composite candidate keys make the tenant/execution/snapshot ownership
    # checks database-enforced rather than application conventions.
    op.create_unique_constraint(
        "uq_business_decision_finalization_id_execution_company",
        "business_workflow_decision_finalizations",
        ["id", "execution_id", "company_id"],
    )
    op.create_unique_constraint(
        "uq_decision_snapshots_id_company",
        "decision_snapshots",
        ["id", "company_id"],
    )
    op.create_table(
        "business_workflow_decision_snapshot_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("is_deleted", sa.Boolean()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_finalization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("material_code", sa.String(128), nullable=False),
        sa.Column("demand_type", sa.String(16), nullable=False),
        sa.Column("decision_context", sa.String(64), nullable=False),
        sa.Column("decision_cutoff_period", sa.String(8), nullable=False),
        sa.ForeignKeyConstraint(
            ("execution_id", "company_id"),
            ("runtime_executions.execution_id", "runtime_executions.company_id"),
            ondelete="RESTRICT",
            name="fk_bw_dsref_execution_company",
        ),
        sa.ForeignKeyConstraint(
            ("decision_finalization_id", "execution_id", "company_id"),
            ("business_workflow_decision_finalizations.id", "business_workflow_decision_finalizations.execution_id", "business_workflow_decision_finalizations.company_id"),
            ondelete="RESTRICT",
            name="fk_bw_dsref_finalization_execution_company",
        ),
        sa.ForeignKeyConstraint(
            ("decision_snapshot_id", "company_id"),
            ("decision_snapshots.id", "decision_snapshots.company_id"),
            ondelete="RESTRICT",
            name="fk_bw_dsref_snapshot_company",
        ),
        sa.UniqueConstraint(
            "company_id", "execution_id", "material_code", "demand_type", "decision_context",
            name="uq_business_decision_snapshot_reference_execution_scope",
        ),
    )
    op.create_index(
        "ix_business_decision_snapshot_reference_execution",
        "business_workflow_decision_snapshot_references",
        ["company_id", "execution_id", "material_code"],
    )
    op.execute("""CREATE FUNCTION business_workflow_decision_snapshot_reference_reject_update()
    RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'BusinessWorkflowDecisionSnapshotReference is immutable'; END; $$""")
    op.execute("""CREATE TRIGGER trg_business_workflow_decision_snapshot_reference_immutable
    BEFORE UPDATE ON business_workflow_decision_snapshot_references
    FOR EACH ROW EXECUTE FUNCTION business_workflow_decision_snapshot_reference_reject_update()""")


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_business_workflow_decision_snapshot_reference_immutable ON business_workflow_decision_snapshot_references")
    op.drop_index("ix_business_decision_snapshot_reference_execution", table_name="business_workflow_decision_snapshot_references")
    op.drop_table("business_workflow_decision_snapshot_references")
    op.execute("DROP FUNCTION IF EXISTS business_workflow_decision_snapshot_reference_reject_update()")
    op.drop_constraint("uq_decision_snapshots_id_company", "decision_snapshots", type_="unique")
    op.drop_constraint("uq_business_decision_finalization_id_execution_company", "business_workflow_decision_finalizations", type_="unique")
