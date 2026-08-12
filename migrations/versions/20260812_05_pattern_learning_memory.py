"""Add durable current Pattern Learning Memory projection."""
from alembic import op
revision='20260812_05';down_revision='20260812_04';branch_labels=None;depends_on=None
def upgrade():
 from app.models.pattern_learning_memory import PatternLearningMemory
 PatternLearningMemory.__table__.create(bind=op.get_bind())
def downgrade():
 from app.models.pattern_learning_memory import PatternLearningMemory
 PatternLearningMemory.__table__.drop(bind=op.get_bind())
