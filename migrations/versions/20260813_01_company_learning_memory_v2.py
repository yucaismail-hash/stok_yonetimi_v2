"""Add canonical Company Learning V2 current projection."""
from alembic import op
revision='20260813_01';down_revision='20260812_05';branch_labels=None;depends_on=None
def upgrade():
 from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
 CompanyLearningMemoryV2.__table__.create(bind=op.get_bind())
def downgrade():
 from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
 CompanyLearningMemoryV2.__table__.drop(bind=op.get_bind())
