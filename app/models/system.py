# app/models/system.py
"""
System models - Algorithm versions, feature flags, system settings.
Follows DOCUMENT 03 - Database Architecture Specification.
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.base import BaseModel


class AlgorithmVersion(BaseModel):
    """
    DOCUMENT 03 Part 02 - Algorithm Version
    Stores analytical engine versions.
    """
    __tablename__ = "algorithm_versions"

    # Algorithm metadata
    name = Column(String, nullable=False)  # forecast, safety_stock, simulation, backtest, supplier
    version = Column(String, nullable=False)  # 1.0.0, 1.2.3, etc.
    
    # Details
    description = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    parameters = Column(JSONB, nullable=True, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    released_by = Column(String, nullable=True)
    released_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AlgorithmVersion {self.name} v{self.version}>"


class FeatureFlag(BaseModel):
    """
    DOCUMENT 03 Part 02 - Feature Flag
    Stores feature activation.
    """
    __tablename__ = "feature_flags"

    # Feature metadata
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    is_enabled = Column(Boolean, default=False)
    
    # Scope
    scope = Column(String, default="global")  # global, company, user
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Rollout
    rollout_percentage = Column(Float, default=100.0)  # 0-100
    rollout_started_at = Column(DateTime(timezone=True), nullable=True)
    rollout_ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Relationships
    company = relationship("Company")
    user = relationship("User")

    def __repr__(self):
        return f"<FeatureFlag {self.key}: {self.is_enabled}>"


class SystemSetting(BaseModel):
    """
    DOCUMENT 03 Part 02 - System Setting
    Stores configurable platform settings.
    """
    __tablename__ = "system_settings"

    # Setting metadata
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Value
    value = Column(JSONB, nullable=False)  # Can store any type
    value_type = Column(String, default="string")  # string, integer, float, boolean, json
    
    # Category
    category = Column(String, default="general")  # general, ai, execution, security, cache, external
    
    # Status
    is_active = Column(Boolean, default=True)
    is_editable = Column(Boolean, default=True)
    
    # Metadata
    updated_by = Column(String, nullable=True)

    def __repr__(self):
        return f"<SystemSetting {self.key}: {self.value}>"