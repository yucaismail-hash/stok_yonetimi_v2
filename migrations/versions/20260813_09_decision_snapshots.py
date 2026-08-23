"""Add immutable canonical Decision Snapshot audit vintages."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260813_09"
down_revision = "20260813_08"
branch_labels = None
depends_on = None


def _immutable_trigger(table):
    op.execute(f"""CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE ON {table}
    FOR EACH ROW EXECUTE FUNCTION decision_snapshot_reject_update()""")


def upgrade():
    op.create_table("decision_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("is_deleted", sa.Boolean()), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("deleted_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("material_code", sa.String(128), nullable=False), sa.Column("demand_type", sa.String(16), nullable=False), sa.Column("decision_context", sa.String(64), nullable=False), sa.Column("decision_cutoff_period", sa.String(8), nullable=False),
        sa.Column("decision_policy_version", sa.String(64), nullable=False), sa.Column("confidence_policy_version", sa.String(64), nullable=False), sa.Column("decision_evidence_fingerprint", sa.String(64), nullable=False), sa.Column("decision_policy_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False), sa.Column("agreement_status", sa.String(32), nullable=False), sa.Column("confidence", sa.Numeric(18,10), nullable=False),
        sa.Column("supporting_evidence", postgresql.JSONB(), nullable=False), sa.Column("conflicting_evidence", postgresql.JSONB(), nullable=False), sa.Column("uncertainty_codes", postgresql.JSONB(), nullable=False), sa.Column("source_provenance", postgresql.JSONB(), nullable=False), sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("company_id","material_code","demand_type","decision_context","decision_cutoff_period","decision_policy_version","decision_evidence_fingerprint","decision_policy_fingerprint", name="uq_decision_snapshot_semantic_identity"))
    op.create_table("decision_snapshot_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("is_deleted", sa.Boolean()), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("deleted_by", postgresql.UUID(as_uuid=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("decision_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decision_snapshots.id", ondelete="RESTRICT"), nullable=False), sa.Column("ordinal", sa.Integer(), nullable=False), sa.Column("candidate_type", sa.String(64), nullable=False), sa.Column("severity", sa.String(16), nullable=False), sa.Column("priority", sa.Integer(), nullable=False), sa.Column("reason_codes", postgresql.JSONB(), nullable=False), sa.Column("supporting_evidence", postgresql.JSONB(), nullable=False), sa.Column("conflicting_evidence", postgresql.JSONB(), nullable=False), sa.Column("confidence", sa.Numeric(18,10), nullable=False), sa.Column("expected_impact_references", postgresql.JSONB(), nullable=False), sa.Column("what_would_change_this", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("decision_snapshot_id", "ordinal", name="uq_decision_snapshot_candidate_ordinal"))
    op.execute("""CREATE FUNCTION decision_snapshot_reject_update() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'DecisionSnapshot is immutable'; END; $$""")
    _immutable_trigger("decision_snapshots"); _immutable_trigger("decision_snapshot_candidates")


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_decision_snapshot_candidates_immutable ON decision_snapshot_candidates")
    op.execute("DROP TRIGGER IF EXISTS trg_decision_snapshots_immutable ON decision_snapshots")
    op.drop_table("decision_snapshot_candidates"); op.drop_table("decision_snapshots")
    op.execute("DROP FUNCTION IF EXISTS decision_snapshot_reject_update()")
