"""Add durable current Supplier Learning Memory projection."""
from alembic import op

revision = "20260813_04"
down_revision = "20260813_03"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.supplier_learning_memory import SupplierLearningMemory
    SupplierLearningMemory.__table__.create(bind=op.get_bind())


def downgrade():
    from app.models.supplier_learning_memory import SupplierLearningMemory
    SupplierLearningMemory.__table__.drop(bind=op.get_bind())
