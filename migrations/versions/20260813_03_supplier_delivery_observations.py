"""Add canonical observed supplier-delivery and correction lineage tables."""
from alembic import op

revision = "20260813_03"
down_revision = "20260813_02"
branch_labels = None
depends_on = None


def upgrade():
    from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision
    bind = op.get_bind()
    SupplierDeliveryObservation.__table__.create(bind=bind)
    SupplierDeliveryObservationRevision.__table__.create(bind=bind)


def downgrade():
    from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision
    bind = op.get_bind()
    SupplierDeliveryObservationRevision.__table__.drop(bind=bind)
    SupplierDeliveryObservation.__table__.drop(bind=bind)
