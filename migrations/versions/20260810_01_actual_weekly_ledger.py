"""Add canonical weekly actual observations and append-only revision ledger."""
from alembic import op
import sqlalchemy as sa

revision = "20260810_01"
down_revision = "20260807_01"
branch_labels = None
depends_on = None

def upgrade():
    from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
    bind = op.get_bind()
    ActualWeeklyObservation.__table__.create(bind=bind)
    ActualWeeklyRevision.__table__.create(bind=bind)
    op.add_column("user_materials", sa.Column("product_level", sa.String(length=32), nullable=True))
    op.add_column("user_materials", sa.Column("product_class", sa.String(), nullable=True))

def downgrade():
    from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
    bind = op.get_bind()
    op.drop_column("user_materials", "product_class")
    op.drop_column("user_materials", "product_level")
    ActualWeeklyRevision.__table__.drop(bind=bind)
    ActualWeeklyObservation.__table__.drop(bind=bind)
