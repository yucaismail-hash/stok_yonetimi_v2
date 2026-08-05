"""
ArtifactPersistenceService - DOCUMENT 06A REVISION 06
Orchestration layer for AI Artifact persistence.

ArtifactPersistenceService SHALL be responsible for:
- Validation workflow
- Version management
- Artifact lifecycle
- Persistence orchestration
- Reuse decisions
- Immutability enforcement
- Calling ArtifactRepository

Repository SHALL remain a pure data access layer.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.artifact import AIArtifact
from app.repositories.artifact_repository import ArtifactRepository
from app.services.artifact.artifact_validator import ArtifactValidator
from app.services.artifact.artifact_version_manager import ArtifactVersionManager
from app.services.artifact.artifact_reuse_manager import ArtifactReuseManager
from app.services.artifact.artifact_metadata_manager import ArtifactMetadataManager


class ArtifactPersistenceService:
    """
    Orchestration layer for persisting AI Artifacts.
    """
    
    def __init__(self, repository: ArtifactRepository):
        self.repository = repository
        self.validator = ArtifactValidator()
        self.version_manager = ArtifactVersionManager()
        self.reuse_manager = ArtifactReuseManager(repository)
        self.metadata_manager = ArtifactMetadataManager()
    
    def persist(self, artifact: AIArtifact) -> AIArtifact:
        """
        Persist an AI Artifact through the complete pipeline.
        
        Pipeline:
        1. Validate
        2. Check for reuse
        3. Manage versions
        4. Persist through repository
        5. Update status
        """
        # Step 1: Validate
        validation = self.validator.validate(artifact)
        if not validation.get("is_valid"):
            artifact.status = "draft"
            artifact.validation_status = "failed"
            artifact.validation_errors = validation.get("errors", [])
            # Still save but with failed validation status
            return self.repository.create(**artifact.__dict__)
        
        artifact.validation_status = "passed"
        artifact.validation_errors = None
        
        # Step 2: Check for reuse
        reusable = self.reuse_manager.find_reusable_artifact(
            company_id=artifact.company_id,
            artifact_type=artifact.artifact_type,
            dataset_id=artifact.dataset_id,
            execution_id=artifact.execution_id
        )
        
        if reusable:
            artifact.is_reused = True
            artifact.reused_from_artifact_id = reusable.id
            artifact.reuse_count = (reusable.reuse_count or 0) + 1
        
        # Step 3: Manage versions
        artifact.artifact_version = self.version_manager.get_next_artifact_version(artifact)
        
        # Step 4: Persist through repository
        persisted = self.repository.create(**artifact.__dict__)
        
        # Step 5: Update status
        if artifact.status == "draft":
            artifact.status = "validated"
        
        return persisted
    
    def publish(self, artifact_id: UUID, published_by: UUID) -> Optional[AIArtifact]:
        """
        Publish an artifact.
        
        After publication, artifact becomes immutable.
        """
        artifact = self.repository.get_by_id(artifact_id)
        if not artifact:
            return None
        
        # Ensure immutability
        if artifact.status == "published":
            raise ValueError("Artifact is already published and immutable")
        
        artifact.status = "published"
        artifact.validated_at = datetime.utcnow()
        artifact.validated_by = published_by
        
        return self.repository.update(artifact, **artifact.__dict__)
    
    def archive(self, artifact_id: UUID) -> Optional[AIArtifact]:
        """
        Archive an artifact.
        """
        artifact = self.repository.get_by_id(artifact_id)
        if not artifact:
            return None
        
        artifact.status = "archived"
        return self.repository.update(artifact, **artifact.__dict__)
    
    def get_latest(self, company_id: UUID, artifact_type: str, dataset_id: Optional[UUID] = None) -> Optional[AIArtifact]:
        """
        Get the latest published artifact of a type.
        """
        return self.repository.get_latest_version(company_id, artifact_type, dataset_id)
    
    def get_by_execution(self, execution_id: UUID) -> Optional[AIArtifact]:
        """
        Get artifact by execution ID.
        """
        return self.repository.get_by_execution(execution_id)
    
    def reuse_artifact(self, artifact_id: UUID, company_id: UUID) -> Optional[AIArtifact]:
        """
        Reuse an existing artifact.
        """
        artifact = self.repository.get_by_id(artifact_id)
        if not artifact:
            return None
        
        # Check if artifact is reusable
        if artifact.status != "published":
            raise ValueError("Only published artifacts can be reused")
        
        # Increment reuse count
        artifact.reuse_count = (artifact.reuse_count or 0) + 1
        return self.repository.update(artifact, **artifact.__dict__)