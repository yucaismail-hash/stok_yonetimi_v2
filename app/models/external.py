# app/models/external.py
"""
External Models - External data cache
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ExternalCache(Base):
    """
    External data cache.
    DOCUMENT 01 - Downloaded external datasets MUST be cached.
    """
    __tablename__ = "external_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, nullable=False, index=True)
    service_name = Column(String, nullable=False)
    cached_data = Column(JSONB, nullable=False)
    data_hash = Column(String(16), nullable=False)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    is_valid = Column(Boolean, default=True)
    hit_count = Column(Integer, default=0)
