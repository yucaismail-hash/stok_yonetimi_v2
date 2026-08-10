"""Add durable Forecast-to-Actual evaluation evidence."""
from alembic import op

revision = "20260810_03"
down_revision = "20260810_02"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
    bind = op.get_bind()
    ForecastEvaluation.__table__.create(bind=bind)
    ForecastEvaluationPoint.__table__.create(bind=bind)


def downgrade():
    from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
    bind = op.get_bind()
    ForecastEvaluationPoint.__table__.drop(bind=bind)
    ForecastEvaluation.__table__.drop(bind=bind)
