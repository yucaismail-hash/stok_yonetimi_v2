"""Add immutable XGBoost Challenger model artifact metadata."""

from alembic import op


revision = "20260810_04"
down_revision = "20260810_03"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.model_artifact import ModelArtifact

    ModelArtifact.__table__.create(bind=op.get_bind())


def downgrade():
    from app.models.model_artifact import ModelArtifact

    ModelArtifact.__table__.drop(bind=op.get_bind())
