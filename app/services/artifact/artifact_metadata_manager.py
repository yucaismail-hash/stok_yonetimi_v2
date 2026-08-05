"""
ArtifactMetadataManager - DOCUMENT 06A AA-006
Metadata management for AI Artifacts.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from app.models.artifact import AIArtifact


class ArtifactMetadataManager:
    """
    Manages metadata for AI Artifacts.
    """
    
    def set_llm_metadata(
        self,
        artifact: AIArtifact,
        provider: str,
        model: str,
        version: Optional[str] = None
    ) -> AIArtifact:
        """Set LLM provider and model metadata."""
        artifact.llm_provider = provider
        artifact.llm_model = model
        if version:
            artifact.model_version = version
        return artifact
    
    def set_version_metadata(
        self,
        artifact: AIArtifact,
        prompt_version: str,
        schema_version: str = "1.0",
        contract_version: str = "1.0"
    ) -> AIArtifact:
        """Set version metadata."""
        artifact.prompt_version = prompt_version
        artifact.schema_version = schema_version
        artifact.communication_contract_version = contract_version
        return artifact
    
    def set_language(self, artifact: AIArtifact, language: str) -> AIArtifact:
        """Set language."""
        artifact.language = language
        return artifact
    
    def get_artifact_context(self, artifact: AIArtifact) -> Dict[str, Any]:
        """Get artifact context as dict."""
        return {
            "id": str(artifact.id) if artifact.id else None,
            "type": artifact.artifact_type,
            "subtype": artifact.artifact_subtype,
            "company_id": str(artifact.company_id),
            "dataset_id": str(artifact.dataset_id) if artifact.dataset_id else None,
            "execution_id": str(artifact.execution_id) if artifact.execution_id else None,
            "language": artifact.language,
            "status": artifact.status,
            "version": artifact.artifact_version,
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
            "generated_at": artifact.generated_at.isoformat() if artifact.generated_at else None
        }