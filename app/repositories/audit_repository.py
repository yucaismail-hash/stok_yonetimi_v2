# app/repositories/audit_repository.py
"""
Audit Repository
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, SecurityEvent
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog entity."""

    def __init__(self, db: Session):
        super().__init__(db, AuditLog)

    def get_by_company(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a company."""
        return self.db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.is_deleted == False
        ).order_by(
            AuditLog.created_at.desc()
        ).offset(skip).limit(limit).all()

    def get_by_event_type(self, company_id: UUID, event_type: str) -> List[AuditLog]:
        """Get audit logs by event type."""
        return self.db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.event_type == event_type,
            AuditLog.is_deleted == False
        ).all()

    def get_by_user(self, user_id: UUID) -> List[AuditLog]:
        """Get audit logs by user."""
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.is_deleted == False
        ).all()

    def get_by_target(self, target_type: str, target_id: UUID) -> List[AuditLog]:
        """Get audit logs by target."""
        return self.db.query(AuditLog).filter(
            AuditLog.target_type == target_type,
            AuditLog.target_id == target_id,
            AuditLog.is_deleted == False
        ).all()


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    """Repository for SecurityEvent entity."""

    def __init__(self, db: Session):
        super().__init__(db, SecurityEvent)

    def get_by_severity(self, severity: str, company_id: Optional[UUID] = None) -> List[SecurityEvent]:
        """Get security events by severity."""
        query = self.db.query(SecurityEvent).filter(
            SecurityEvent.severity == severity,
            SecurityEvent.is_deleted == False
        )
        if company_id:
            query = query.filter(SecurityEvent.company_id == company_id)
        return query.all()

    def get_unresolved(self, company_id: Optional[UUID] = None) -> List[SecurityEvent]:
        """Get unresolved security events."""
        query = self.db.query(SecurityEvent).filter(
            SecurityEvent.resolved == False,
            SecurityEvent.is_deleted == False
        )
        if company_id:
            query = query.filter(SecurityEvent.company_id == company_id)
        return query.all()