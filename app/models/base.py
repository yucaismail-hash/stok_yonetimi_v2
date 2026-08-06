# app/models/base.py
"""
Base model for all database entities.
Follows DOCUMENT 03 - Database Architecture Specification.
"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declared_attr
from uuid_extensions import uuid7
from datetime import datetime

from app.database import Base


class BaseModel(Base):
    """Base model with UUID primary key and common fields."""
    
    __abstract__ = True

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7)
    
    # Soft Delete fields (DOCUMENT 03 - Section 9)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(PG_UUID(as_uuid=True), nullable=True)  # User ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def soft_delete(self, user_id):
        """Soft delete this entity."""
        self.is_deleted = True
        self.deleted_at = datetime.now()
        self.deleted_by = user_id

    def restore(self):
        """Restore soft deleted entity."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
