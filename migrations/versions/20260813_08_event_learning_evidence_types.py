"""Allow canonical Event Observation learning evidence types."""
from alembic import op
revision='20260813_08';down_revision='20260813_07';branch_labels=None;depends_on=None
_NEW="event_type IN ('ACTUAL_ACCEPTED', 'ACTUAL_CORRECTED', 'FORECAST_EVALUATED', 'CHAMPION_PROMOTED', 'CHAMPION_ROLLED_BACK', 'RETRAINING_COMPLETED', 'SUPPLIER_DELIVERY_OBSERVED', 'SUPPLIER_DELIVERY_CORRECTED', 'EVENT_OBSERVED', 'EVENT_CORRECTED', 'EVENT_CANCELLED')"
_OLD="event_type IN ('ACTUAL_ACCEPTED', 'ACTUAL_CORRECTED', 'FORECAST_EVALUATED', 'CHAMPION_PROMOTED', 'CHAMPION_ROLLED_BACK', 'RETRAINING_COMPLETED', 'SUPPLIER_DELIVERY_OBSERVED', 'SUPPLIER_DELIVERY_CORRECTED')"
def upgrade():
 op.drop_constraint('ck_learning_evidence_event_type','learning_evidence',type_='check');op.create_check_constraint('ck_learning_evidence_event_type','learning_evidence',_NEW)
def downgrade():
 op.drop_constraint('ck_learning_evidence_event_type','learning_evidence',type_='check');op.create_check_constraint('ck_learning_evidence_event_type','learning_evidence',_OLD)
