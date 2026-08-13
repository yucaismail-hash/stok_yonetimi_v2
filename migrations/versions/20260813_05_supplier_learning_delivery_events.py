"""Permit canonical supplier delivery LearningEvidence events."""
from alembic import op

revision = "20260813_05"
down_revision = "20260813_04"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_learning_evidence_event_type", "learning_evidence", type_="check")
    op.create_check_constraint("ck_learning_evidence_event_type", "learning_evidence",
        "event_type IN ('ACTUAL_ACCEPTED', 'ACTUAL_CORRECTED', 'FORECAST_EVALUATED', 'CHAMPION_PROMOTED', 'CHAMPION_ROLLED_BACK', 'RETRAINING_COMPLETED', 'SUPPLIER_DELIVERY_OBSERVED', 'SUPPLIER_DELIVERY_CORRECTED')")


def downgrade():
    op.drop_constraint("ck_learning_evidence_event_type", "learning_evidence", type_="check")
    op.create_check_constraint("ck_learning_evidence_event_type", "learning_evidence",
        "event_type IN ('ACTUAL_ACCEPTED', 'ACTUAL_CORRECTED', 'FORECAST_EVALUATED', 'CHAMPION_PROMOTED', 'CHAMPION_ROLLED_BACK', 'RETRAINING_COMPLETED')")
