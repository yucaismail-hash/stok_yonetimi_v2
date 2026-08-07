"""Add canonical durable runtime tables (ADR-029 through ADR-032)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260807_01"
down_revision = "20260806_01"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.runtime import RuntimeCheckpoint, RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt

    bind = op.get_bind()
    for table in (RuntimeExecution.__table__, RuntimeTask.__table__, RuntimeTaskAttempt.__table__, RuntimeCheckpoint.__table__, RuntimeResultReference.__table__):
        table.create(bind=bind)


def downgrade():
    from app.models.runtime import RuntimeCheckpoint, RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt

    bind = op.get_bind()
    for table in (RuntimeResultReference.__table__, RuntimeCheckpoint.__table__, RuntimeTaskAttempt.__table__, RuntimeTask.__table__, RuntimeExecution.__table__):
        table.drop(bind=bind)
