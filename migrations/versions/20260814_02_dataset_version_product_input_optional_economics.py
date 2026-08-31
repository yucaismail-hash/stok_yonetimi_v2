"""Allow unknown optional V3 economic inputs without fabricating values."""
from alembic import op
import sqlalchemy as sa


revision = "20260814_02"
down_revision = "20260814_01"
branch_labels = None
depends_on = None


def upgrade():
    for column, precision, scale in (("unit_cost", 18, 4), ("holding_rate", 18, 8), ("stockout_cost", 18, 4)):
        op.alter_column(
            "dataset_version_product_inputs",
            column,
            existing_type=sa.Numeric(precision, scale),
            nullable=True,
        )


def downgrade():
    # PostgreSQL deliberately rejects this downgrade while unknown/null economics exist.
    # No default value is introduced because NULL and an explicit zero have distinct meaning.
    for column, precision, scale in (("unit_cost", 18, 4), ("holding_rate", 18, 8), ("stockout_cost", 18, 4)):
        op.alter_column(
            "dataset_version_product_inputs",
            column,
            existing_type=sa.Numeric(precision, scale),
            nullable=False,
        )
