"""Add durable correction-safe retraining candidate jobs."""

from alembic import op


revision = "20260811_03"
down_revision = "20260811_02"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.retraining_job import RetrainingJob
    RetrainingJob.__table__.create(bind=op.get_bind())


def downgrade():
    from app.models.retraining_job import RetrainingJob
    RetrainingJob.__table__.drop(bind=op.get_bind())
