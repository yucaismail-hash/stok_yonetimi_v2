# app/models/security.py
"""
Security models - Encryption key management.
Follows DOCUMENT 03 - Database Architecture Specification.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class CompanyEncryptionKey(BaseModel):
    """
    DOCUMENT 01: Security
    Every company owns an independent Encryption Key.
    """
    __tablename__ = "company_encryption_keys"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, unique=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    encrypted_key = Column(Text, nullable=False)
    key_version = Column(String, default="1")
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, default=1)

    # Relationships
    company = relationship("Company", back_populates="encryption_key")
    user = relationship("User", back_populates="encryption_key")