"""
ArtifactVersionManager - DOCUMENT 06A AA-005
Version management for AI Artifacts.

Every AI Artifact SHALL support:
- Artifact Version
- Prompt Version
- Schema Version
- Communication Contract Version
- LLM Version
"""

from typing import Optional
from uuid import UUID
from app.models.artifact import AIArtifact


class ArtifactVersionManager:
    """
    Manages versioning for AI Artifacts.
    """
    
    def get_next_artifact_version(self, artifact: AIArtifact) -> int:
        """
        Calculate the next artifact version.
        
        If artifact is a new version of an existing artifact,
        increment the version number.
        """
        if artifact.artifact_version:
            return artifact.artifact_version + 1
        return 1
    
    def set_prompt_version(self, artifact: AIArtifact, prompt_version: str) -> AIArtifact:
        """Set prompt version."""
        artifact.prompt_version = prompt_version
        return artifact
    
    def set_schema_version(self, artifact: AIArtifact, schema_version: str) -> AIArtifact:
        """Set schema version."""
        artifact.schema_version = schema_version
        return artifact
    
    def set_communication_contract_version(self, artifact: AIArtifact, version: str) -> AIArtifact:
        """Set communication contract version."""
        artifact.communication_contract_version = version
        return artifact
    
    def set_llm_version(self, artifact: AIArtifact, provider: str, model: str, version: str) -> AIArtifact:
        """Set LLM provider and model version."""
        artifact.llm_provider = provider
        artifact.llm_model = model
        artifact.model_version = version
        return artifact
    
    def increment_version(self, artifact: AIArtifact) -> AIArtifact:
        """Increment artifact version."""
        artifact.artifact_version = (artifact.artifact_version or 0) + 1
        return artifact