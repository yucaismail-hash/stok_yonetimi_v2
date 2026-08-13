"""Canonical company-scoped current Learning evidence projection."""
from sqlalchemy import Column,DateTime,ForeignKey,Integer,Numeric,String,UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB,UUID as PG_UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel
class CompanyLearningMemoryV2(BaseModel):
 __tablename__='company_learning_memory_v2'
 company_id=Column(PG_UUID(as_uuid=True),ForeignKey('companies.id',ondelete='RESTRICT'),nullable=False,unique=True)
 company_learning_policy_version=Column(String(32),nullable=False);learning_score_policy_version=Column(String(32),nullable=False)
 evidence_count=Column(Integer,nullable=False);evidence_type_counts=Column(JSONB,nullable=False);evidence_source_diversity=Column(Integer,nullable=False);material_scope_count=Column(Integer,nullable=False);demand_scope_count=Column(Integer,nullable=False);pattern_memory_scope_count=Column(Integer,nullable=False);forecast_evaluated_scope_count=Column(Integer,nullable=False);forecast_evaluation_sample_count=Column(Integer,nullable=False);pattern_distribution=Column(JSONB,nullable=False);accepted_correction_evidence_count=Column(Integer,nullable=False);retraining_summary=Column(JSONB,nullable=False);champion_summary=Column(JSONB,nullable=False)
 latest_evidence_at=Column(DateTime(timezone=True),nullable=True);oldest_evidence_at=Column(DateTime(timezone=True),nullable=True);evidence_maturity_score=Column(Numeric(8,3),nullable=False);evidence_maturity_level=Column(String(16),nullable=False);source_summary_fingerprint=Column(String(64),nullable=False);last_materialized_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now());row_version=Column(Integer,nullable=False,default=1)
