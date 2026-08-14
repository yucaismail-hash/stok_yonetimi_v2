"""Add durable current Event Intelligence Memory projection."""
from alembic import op
revision='20260813_07';down_revision='20260813_06';branch_labels=None;depends_on=None
def upgrade():
 from app.models.event_intelligence_memory import EventIntelligenceMemory
 EventIntelligenceMemory.__table__.create(bind=op.get_bind())
def downgrade():
 from app.models.event_intelligence_memory import EventIntelligenceMemory
 EventIntelligenceMemory.__table__.drop(bind=op.get_bind())
