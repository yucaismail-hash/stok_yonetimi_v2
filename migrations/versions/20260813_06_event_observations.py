"""Add canonical Event Observation ledger and revision lineage."""
from alembic import op

revision = "20260813_06"
down_revision = "20260813_05"
branch_labels = None
depends_on = None

def upgrade():
    from app.models.event_observation import EventObservation, EventRevision
    bind = op.get_bind(); EventObservation.__table__.create(bind=bind); EventRevision.__table__.create(bind=bind)

def downgrade():
    from app.models.event_observation import EventObservation, EventRevision
    bind = op.get_bind(); EventRevision.__table__.drop(bind=bind); EventObservation.__table__.drop(bind=bind)
