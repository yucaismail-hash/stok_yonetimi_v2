"""Add immutable V3 operational product inputs."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260814_01"
down_revision = "20260813_13"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("dataset_version_product_inputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("is_deleted", sa.Boolean()), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("deleted_by", postgresql.UUID(as_uuid=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False), sa.Column("dataset_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dataset_versions.id", ondelete="RESTRICT"), nullable=False), sa.Column("material_code", sa.String(128), nullable=False), sa.Column("product_name", sa.String(256)), sa.Column("product_group", sa.String(128)), sa.Column("product_class", sa.String(128)), sa.Column("product_level", sa.String(32), nullable=False),
        sa.Column("initial_stock", sa.Numeric(18,4), nullable=False), sa.Column("lead_time_days", sa.Numeric(18,4), nullable=False), sa.Column("lot_size", sa.Numeric(18,4), nullable=False), sa.Column("unit_cost", sa.Numeric(18,4), nullable=False), sa.Column("holding_rate", sa.Numeric(18,8), nullable=False), sa.Column("stockout_cost", sa.Numeric(18,4), nullable=False),
        sa.UniqueConstraint("dataset_version_id","material_code", name="uq_dataset_version_product_input"), sa.CheckConstraint("product_level IN ('finished_good','semi_finished_good','raw_material')", name="ck_dataset_version_product_input_level"), sa.CheckConstraint("initial_stock >= 0 AND lead_time_days > 0 AND lot_size >= 0 AND unit_cost >= 0 AND holding_rate >= 0 AND stockout_cost >= 0", name="ck_dataset_version_product_input_nonnegative"))
    op.create_index("ix_dataset_version_product_input_company_version_material", "dataset_version_product_inputs", ["company_id","dataset_version_id","material_code"])

def downgrade():
    op.drop_index("ix_dataset_version_product_input_company_version_material", table_name="dataset_version_product_inputs")
    op.drop_table("dataset_version_product_inputs")
