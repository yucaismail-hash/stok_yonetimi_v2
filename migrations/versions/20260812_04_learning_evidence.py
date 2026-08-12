"""Add immutable canonical Learning Evidence lineage."""

from alembic import op


revision = "20260812_04"
down_revision = "20260812_03"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.learning_evidence import LearningEvidence
    LearningEvidence.__table__.create(bind=op.get_bind())


def downgrade():
    from app.models.learning_evidence import LearningEvidence
    LearningEvidence.__table__.drop(bind=op.get_bind())
