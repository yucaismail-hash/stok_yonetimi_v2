"""Harden Decision feedback idempotency with a NULL-safe semantic key."""
from alembic import op
import sqlalchemy as sa

revision = "20260813_11"
down_revision = "20260813_10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("decision_feedback_events", sa.Column("semantic_key", sa.String(128), nullable=True))
    op.execute("""UPDATE decision_feedback_events SET semantic_key = feedback_fingerprint || ':' || COALESCE(supersedes_feedback_id::text, 'root')""")
    op.alter_column("decision_feedback_events", "semantic_key", nullable=False)
    op.create_unique_constraint("uq_decision_feedback_company_semantic_key", "decision_feedback_events", ["company_id", "semantic_key"])


def downgrade():
    op.drop_constraint("uq_decision_feedback_company_semantic_key", "decision_feedback_events", type_="unique")
    op.drop_column("decision_feedback_events", "semantic_key")
