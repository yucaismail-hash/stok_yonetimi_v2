"""
AI Artifact Repository - DOCUMENT 06A AA-002
Centralized AI Artifact Repository

REVISION 06: Repository SHALL be responsible only for:
- CRUD operations
- Database queries
- Transactions
- Persistence access
- Version retrieval
- Filtering
- Database interaction

Repository SHALL NEVER contain:
- Business rules
- Validation
- Artifact creation
- Reuse decisions
- Version calculation
- Workflow logic
"""

from typing import Optional, List, Dict, Any, func
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.models.artifact import AIArtifact
from app.repositories.base import BaseRepository


class ArtifactRepository(BaseRepository):
    """
    Pure data access layer for AI Artifacts.
    No business logic, validation, or orchestration.
    """
    
    def __init__(self, db: Session):
        super().__init__(AIArtifact, db)
    
    # ====================================================================
    # CRUD OPERATIONS
    # ====================================================================
    
    def create(self, **kwargs) -> AIArtifact:
        """Create a new artifact record."""
        artifact = AIArtifact(**kwargs)
        self.db.add(artifact)
        self.db.flush()
        return artifact
    
    def get_by_id(self, artifact_id: UUID) -> Optional[AIArtifact]:
        """Get artifact by ID."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.id == artifact_id,
            AIArtifact.is_deleted.is_(None)
        ).first()
    
    def update(self, artifact: AIArtifact, **kwargs) -> AIArtifact:
        """Update artifact fields."""
        for key, value in kwargs.items():
            if hasattr(artifact, key):
                setattr(artifact, key, value)
        self.db.flush()
        return artifact
    
    def delete(self, artifact_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete artifact."""
        artifact = self.get_by_id(artifact_id)
        if artifact:
            artifact.is_deleted = func.now()
            artifact.deleted_by = deleted_by
            self.db.flush()
            return True
        return False
    
    # ====================================================================
    # QUERIES - FILTERING
    # ====================================================================
    
    def get_by_company(self, company_id: UUID, limit: int = 100, offset: int = 0) -> List[AIArtifact]:
        """Get all artifacts for a company."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.company_id == company_id,
            AIArtifact.is_deleted.is_(None)
        ).order_by(desc(AIArtifact.created_at)).limit(limit).offset(offset).all()
    
    def get_by_execution(self, execution_id: UUID) -> Optional[AIArtifact]:
        """Get artifact by execution ID."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.execution_id == execution_id,
            AIArtifact.is_deleted.is_(None)
        ).first()
    
    def get_by_dataset(self, dataset_id: UUID) -> List[AIArtifact]:
        """Get all artifacts for a dataset."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.dataset_id == dataset_id,
            AIArtifact.is_deleted.is_(None)
        ).order_by(desc(AIArtifact.created_at)).all()
    
    def get_by_type(self, company_id: UUID, artifact_type: str, limit: int = 50) -> List[AIArtifact]:
        """Get artifacts by type."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.company_id == company_id,
            AIArtifact.artifact_type == artifact_type,
            AIArtifact.is_deleted.is_(None)
        ).order_by(desc(AIArtifact.created_at)).limit(limit).all()
    
    def get_latest_version(self, company_id: UUID, artifact_type: str, dataset_id: Optional[UUID] = None) -> Optional[AIArtifact]:
        """Get the latest version of an artifact type."""
        query = self.db.query(AIArtifact).filter(
            AIArtifact.company_id == company_id,
            AIArtifact.artifact_type == artifact_type,
            AIArtifact.status == "published",
            AIArtifact.is_deleted.is_(None)
        )
        if dataset_id:
            query = query.filter(AIArtifact.dataset_id == dataset_id)
        return query.order_by(desc(AIArtifact.artifact_version)).first()
    
    def get_versions(self, artifact_id: UUID) -> List[AIArtifact]:
        """
        Get all versions of an artifact.
        Note: This is a placeholder. Versioning is handled by artifact_version_manager.
        """
        artifact = self.get_by_id(artifact_id)
        if not artifact:
            return []
        # In a real implementation, versions would be linked.
        # For now, return the single artifact.
        return [artifact]
    
    def get_by_status(self, company_id: UUID, status: str) -> List[AIArtifact]:
        """Get artifacts by status."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.company_id == company_id,
            AIArtifact.status == status,
            AIArtifact.is_deleted.is_(None)
        ).order_by(desc(AIArtifact.created_at)).all()
    
    def get_reusable_artifacts(self, company_id: UUID, artifact_type: str, dataset_id: Optional[UUID] = None) -> List[AIArtifact]:
        """Get published artifacts that can be reused."""
        query = self.db.query(AIArtifact).filter(
            AIArtifact.company_id == company_id,
            AIArtifact.artifact_type == artifact_type,
            AIArtifact.status == "published",
            AIArtifact.is_deleted.is_(None)
        )
        if dataset_id:
            query = query.filter(AIArtifact.dataset_id == dataset_id)
        return query.order_by(desc(AIArtifact.created_at)).all()
    
    # ====================================================================
    # COUNT OPERATIONS
    # ====================================================================
    
    def count_by_company(self, company_id: UUID) -> int:
        """Count artifacts for a company."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.company_id == company_id,
            AIArtifact.is_deleted.is_(None)
        ).count()
    
    def count_by_type(self, company_id: UUID, artifact_type: str) -> int:
        """Count artifacts by type."""
        return self.db.query(AIArtifact).filter(
            AIArtifact.company_id == company_id,
            AIArtifact.artifact_type == artifact_type,
            AIArtifact.is_deleted.is_(None)
        ).count()