# app/models/audit.py
"""
Audit models - Immutable business events and security events.
Follows DOCUMENT 03 - Database Architecture Specification.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """
    DOCUMENT 03 Part 02 - Audit Log
    Stores immutable business events.
    """
    __tablename__ = "audit_logs"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Event metadata
    event_type = Column(String, nullable=False)  # dataset_uploaded, dataset_approved, workflow_started, etc.
    event_category = Column(String, nullable=False, default="business")  # business, security, system
    
    # Event details
    description = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=True)  # Additional context
    
    # Target
    target_type = Column(String, nullable=True)  # dataset, workflow, user, etc.
    target_id = Column(PG_UUID(as_uuid=True), nullable=True)
    
    # IP and user agent
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Relationships
    company = relationship("Company")
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.event_type} - {self.created_at}>"


class SecurityEvent(BaseModel):
    """
    DOCUMENT 03 Part 02 - Security Event
    Stores security related events.
    """
    __tablename__ = "security_events"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)  # Null for system-wide
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Event metadata
    event_type = Column(String, nullable=False)  # auth_failure, permission_denied, encryption_failure, etc.
    severity = Column(String, nullable=False, default="medium")  # low, medium, high, critical
    
    # Event details
    description = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=True)
    
    # Source
    source_ip = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    method = Column(String, nullable=True)
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    company = relationship("Company")
    user = relationship("User")

    def __repr__(self):
        return f"<SecurityEvent {self.event_type} - {self.severity}>"
