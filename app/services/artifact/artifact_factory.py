"""
ArtifactFactory - DOCUMENT 06A REVISION 01
Centralized artifact creation mechanism.

No module SHALL instantiate AIArtifact objects directly.
All communication modules SHALL create artifacts through ArtifactFactory.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.artifact import AIArtifact
from app.services.artifact.artifact_builder import ArtifactBuilder
from app.services.artifact.artifact_validator import ArtifactValidator


class ArtifactFactory:
    """
    Centralized factory for creating AI Artifacts.
    All communication modules SHALL use this factory.
    """
    
    def __init__(self):
        self.builder = ArtifactBuilder()
        self.validator = ArtifactValidator()
    
    def create_analysis_narrative(
        self,
        company_id: UUID,
        execution_id: UUID,
        dataset_id: Optional[UUID],
        content: Dict[str, Any],
        generated_by: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AIArtifact:
        """
        Create an Analysis Narrative artifact.
        
        Artifact Type: analysis_narrative
        """
        return self._create_artifact(
            artifact_type="analysis_narrative",
            artifact_subtype="analysis_narrative",
            company_id=company_id,
            execution_id=execution_id,
            dataset_id=dataset_id,
            content=content,
            generated_by=generated_by,
            metadata=metadata
        )
    
    def create_executive_timeline(
        self,
        company_id: UUID,
        execution_id: UUID,
        dataset_id: Optional[UUID],
        content: Dict[str, Any],
        generated_by: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AIArtifact:
        """
        Create an Executive Timeline artifact.
        
        Artifact Type: executive_timeline
        """
        return self._create_artifact(
            artifact_type="executive_timeline",
            artifact_subtype="executive_timeline",
            company_id=company_id,
            execution_id=execution_id,
            dataset_id=dataset_id,
            content=content,
            generated_by=generated_by,
            metadata=metadata
        )
    
    def create_executive_advisor(
        self,
        company_id: UUID,
        execution_id: UUID,
        dataset_id: Optional[UUID],
        content: Dict[str, Any],
        generated_by: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AIArtifact:
        """
        Create an Executive Advisor artifact.
        
        Artifact Type: executive_advisor
        """
        return self._create_artifact(
            artifact_type="executive_advisor",
            artifact_subtype="executive_advisor",
            company_id=company_id,
            execution_id=execution_id,
            dataset_id=dataset_id,
            content=content,
            generated_by=generated_by,
            metadata=metadata
        )
    
    def _create_artifact(
        self,
        artifact_type: str,
        artifact_subtype: str,
        company_id: UUID,
        execution_id: UUID,
        dataset_id: Optional[UUID],
        content: Dict[str, Any],
        generated_by: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AIArtifact:
        """
        Internal method to build and validate an artifact.
        """
        # Build the artifact
        artifact = self.builder.build(
            artifact_type=artifact_type,
            artifact_subtype=artifact_subtype,
            company_id=company_id,
            execution_id=execution_id,
            dataset_id=dataset_id,
            content=content,
            generated_by=generated_by,
            metadata=metadata or {}
        )
        
        # Validate the artifact
        validation_result = self.validator.validate(artifact)
        if validation_result.get("is_valid"):
            artifact.status = "validated"
            artifact.validation_status = "passed"
        else:
            artifact.status = "draft"
            artifact.validation_status = "failed"
            artifact.validation_errors = validation_result.get("errors", [])
        
        return artifact