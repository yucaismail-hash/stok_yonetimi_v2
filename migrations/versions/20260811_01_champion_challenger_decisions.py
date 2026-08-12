from alembic import op
revision='20260811_01';down_revision='20260810_05';branch_labels=None;depends_on=None
def upgrade():
 from app.models.champion_challenger_decision import ChampionChallengerDecision
 ChampionChallengerDecision.__table__.create(bind=op.get_bind())
def downgrade():
 from app.models.champion_challenger_decision import ChampionChallengerDecision
 ChampionChallengerDecision.__table__.drop(bind=op.get_bind())
