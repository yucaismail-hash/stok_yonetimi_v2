"""Add durable Learning Evidence refresh delivery intents."""
from alembic import op

revision = "20260813_02"
down_revision = "20260813_01"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.learning_refresh_delivery import LearningRefreshDelivery
    LearningRefreshDelivery.__table__.create(bind=op.get_bind())


def downgrade():
    from app.models.learning_refresh_delivery import LearningRefreshDelivery
    LearningRefreshDelivery.__table__.drop(bind=op.get_bind())
