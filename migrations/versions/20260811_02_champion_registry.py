"""Add durable Champion Registry foundation."""
from alembic import op

revision = "20260811_02"
down_revision = "20260811_01"
branch_labels = None
depends_on = None

def upgrade():
    from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
    bind = op.get_bind()
    ChampionRegistryEntry.__table__.create(bind=bind)
    ChampionRegistryCurrent.__table__.create(bind=bind)
    ChampionRegistryTransition.__table__.create(bind=bind)

def downgrade():
    from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
    bind = op.get_bind()
    ChampionRegistryTransition.__table__.drop(bind=bind)
    ChampionRegistryCurrent.__table__.drop(bind=bind)
    ChampionRegistryEntry.__table__.drop(bind=bind)
