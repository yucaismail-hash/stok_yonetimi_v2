"""Mutable current projection of a canonical Pattern Intelligence result."""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel

class PatternLearningMemory(BaseModel):
 __tablename__='pattern_learning_memory'
 company_id=Column(PG_UUID(as_uuid=True),ForeignKey('companies.id',ondelete='RESTRICT'),nullable=False)
 material_code=Column(String(128),nullable=False);demand_type=Column(String(16),nullable=False)
 product_level=Column(String(32),nullable=True);product_group=Column(String(128),nullable=True);product_class=Column(String(128),nullable=True)
 pattern_classification=Column(String(64),nullable=False);pattern_policy_version=Column(String(32),nullable=False);feature_version=Column(String(32),nullable=False);confidence_policy_version=Column(String(32),nullable=False)
 sample_count=Column(Integer,nullable=False);period_start=Column(String(8),nullable=False);period_end=Column(String(8),nullable=False);cutoff_period=Column(String(8),nullable=False);coverage_ratio=Column(Numeric(18,10),nullable=False);missing_period_count=Column(Integer,nullable=False)
 mean_demand=Column(Numeric(18,8),nullable=True);std_demand=Column(Numeric(18,8),nullable=True);coefficient_of_variation=Column(Numeric(18,10),nullable=True);zero_demand_ratio=Column(Numeric(18,10),nullable=False);adi=Column(Numeric(18,10),nullable=True);trend_slope=Column(Numeric(18,10),nullable=True);trend_strength=Column(Numeric(18,10),nullable=True);recent_change_ratio=Column(Numeric(18,10),nullable=True)
 seasonality_status=Column(String(64),nullable=False);confidence=Column(Numeric(18,10),nullable=False);source_pattern_fingerprint=Column(String(64),nullable=False);source_learning_evidence_ids=Column(JSONB,nullable=False,default=list);last_materialized_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now());row_version=Column(Integer,nullable=False,default=1)
 __table_args__=(UniqueConstraint('company_id','material_code','demand_type',name='uq_pattern_learning_memory_scope'),Index('ix_pattern_learning_memory_company_scope','company_id','material_code','demand_type'),)
