"""Add immutable non-authoritative Decision Snapshot user feedback events."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260813_10"
down_revision = "20260813_09"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("decision_feedback_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("is_deleted", sa.Boolean()), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("deleted_by", postgresql.UUID(as_uuid=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("decision_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decision_snapshots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("candidate_ordinal", sa.Integer()), sa.Column("candidate_type", sa.String(64)), sa.Column("feedback_type", sa.String(32), nullable=False), sa.Column("comment", sa.String(1000)), sa.Column("source_metadata", postgresql.JSONB(), nullable=False), sa.Column("supersedes_feedback_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decision_feedback_events.id", ondelete="RESTRICT")), sa.Column("feedback_fingerprint", sa.String(64), nullable=False),
        sa.CheckConstraint("feedback_type IN ('HELPFUL', 'NOT_HELPFUL')", name="ck_decision_feedback_type"),
        sa.UniqueConstraint("company_id", "user_id", "decision_snapshot_id", "candidate_ordinal", "candidate_type", "feedback_type", "feedback_fingerprint", "supersedes_feedback_id", name="uq_decision_feedback_event_semantic_identity"))
    op.execute("""CREATE FUNCTION decision_feedback_reject_update() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'DecisionFeedbackEvent is immutable'; END; $$""")
    op.execute("""CREATE TRIGGER trg_decision_feedback_events_immutable BEFORE UPDATE ON decision_feedback_events FOR EACH ROW EXECUTE FUNCTION decision_feedback_reject_update()""")


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_decision_feedback_events_immutable ON decision_feedback_events")
    op.drop_table("decision_feedback_events")
    op.execute("DROP FUNCTION IF EXISTS decision_feedback_reject_update()")
