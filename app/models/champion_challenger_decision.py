from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from app.models.base import BaseModel

class ChampionChallengerDecision(BaseModel):
 __tablename__='champion_challenger_decisions'
 company_id=Column(PG_UUID(as_uuid=True),ForeignKey('companies.id'),nullable=False); material_code=Column(String(128),nullable=False); demand_type=Column(String(16),nullable=False)
 challenger_model_artifact_id=Column(PG_UUID(as_uuid=True),ForeignKey('model_artifacts.id'),nullable=False); champion_evidence=Column(JSONB,nullable=False); comparison_start_period=Column(String(8),nullable=False); comparison_end_period=Column(String(8),nullable=False); sample_count=Column(Integer,nullable=False)
 champion_metrics=Column(JSONB,nullable=False); challenger_metrics=Column(JSONB,nullable=False); policy_version=Column(String(64),nullable=False); thresholds=Column(JSONB,nullable=False); decision=Column(String(32),nullable=False); reason_codes=Column(JSONB,nullable=False); comparison_fingerprint=Column(String(64),nullable=False)
 __table_args__=(UniqueConstraint('company_id','comparison_fingerprint',name='uq_cc_decision_fingerprint'),)

@event.listens_for(ChampionChallengerDecision, 'before_update')
def _forbid_champion_challenger_decision_update(mapper, connection, target):
 raise ValueError('ChampionChallengerDecision is immutable')
