"""Add immutable Forecast Vintage headers and target-period points."""
from alembic import op
revision='20260810_02'; down_revision='20260810_01'; branch_labels=None; depends_on=None
def upgrade():
 from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
 bind=op.get_bind(); ForecastVintage.__table__.create(bind=bind); ForecastVintagePoint.__table__.create(bind=bind)
def downgrade():
 from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
 bind=op.get_bind(); ForecastVintagePoint.__table__.drop(bind=bind); ForecastVintage.__table__.drop(bind=bind)
