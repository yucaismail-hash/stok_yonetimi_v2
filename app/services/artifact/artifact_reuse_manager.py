"""
ArtifactReuseManager - DOCUMENT 06A AA-009
Reuse decision logic for AI Artifacts.

Previously generated AI Artifacts SHALL always be reused.
Artifacts SHALL NOT be regenerated unless:
- a new analytical execution exists
- or explicit regeneration is requested.
"""

from typing import Optional
from uuid import UUID

from app.models.artifact import AIArtifact
from app.repositories.artifact_repository import ArtifactRepository


class ArtifactReuseManager:
    """
    Manages reuse decisions for AI Artifacts.
    """
    
    def __init__(self, repository: ArtifactRepository):
        self.repository = repository
    
    def find_reusable_artifact(
        self,
        company_id: UUID,
        artifact_type: str,
        dataset_id: Optional[UUID] = None,
        execution_id: Optional[UUID] = None
    ) -> Optional[AIArtifact]:
        """
        Find a reusable artifact.
        
        Returns the latest published artifact if available.
        """
        # Get all reusable artifacts
        artifacts = self.repository.get_reusable_artifacts(company_id, artifact_type, dataset_id)
        
        if not artifacts:
            return None
        
        # If execution_id is provided, check if there's an artifact for this execution
        if execution_id:
            for artifact in artifacts:
                if artifact.execution_id == execution_id:
                    return artifact
        
        # Otherwise return the latest
        return artifacts[0] if artifacts else None
    
    def should_reuse(
        self,
        company_id: UUID,
        artifact_type: str,
        dataset_id: Optional[UUID] = None,
        execution_id: Optional[UUID] = None,
        force_regenerate: bool = False
    ) -> bool:
        """
        Determine if an existing artifact should be reused.
        
        Returns:
            True if reuse is appropriate, False if regeneration needed.
        """
        if force_regenerate:
            return False
        
        artifact = self.find_reusable_artifact(company_id, artifact_type, dataset_id, execution_id)
        return artifact is not None
    
    def get_reusable_artifacts(
        self,
        company_id: UUID,
        artifact_type: str,
        dataset_id: Optional[UUID] = None
    ) -> list:
        """
        Get all reusable artifacts of a type.
        """
        return self.repository.get_reusable_artifacts(company_id, artifact_type, dataset_id)