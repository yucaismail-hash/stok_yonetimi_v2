"""
ArtifactBuilder - DOCUMENT 06A REVISION 02
Constructs AIArtifact objects from content and metadata.

This component constructs AIArtifact objects.
Serialization SHALL remain a future concern for API and export layers.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.artifact import AIArtifact


class ArtifactBuilder:
    """
    Builds AIArtifact objects from raw content and metadata.
    """
    
    def build(
        self,
        artifact_type: str,
        artifact_subtype: str,
        company_id: UUID,
        execution_id: UUID,
        dataset_id: Optional[UUID],
        content: Dict[str, Any],
        generated_by: UUID,
        metadata: Dict[str, Any]
    ) -> AIArtifact:
        """
        Build an AIArtifact object.
        
        Args:
            artifact_type: analysis_narrative, executive_timeline, executive_advisor
            artifact_subtype: Sub-type for future filtering
            company_id: Company ID
            execution_id: Execution ID (UUID only - REVISION 05)
            dataset_id: Dataset ID (optional)
            content: Structured JSON content
            generated_by: User who generated the artifact
            metadata: Additional metadata (LLM provider, model, versions, etc.)
        
        Returns:
            AIArtifact: Constructed artifact object
        """
        # Extract metadata with defaults
        language = metadata.get("language", "tr")
        prompt_version = metadata.get("prompt_version")
        schema_version = metadata.get("schema_version", "1.0")
        communication_contract_version = metadata.get("communication_contract_version", "1.0")
        artifact_version = metadata.get("artifact_version", 1)
        
        llm_provider = metadata.get("llm_provider")
        llm_model = metadata.get("llm_model")
        model_version = metadata.get("model_version")
        
        # Build the artifact
        artifact = AIArtifact(
            artifact_type=artifact_type,
            artifact_subtype=artifact_subtype,
            company_id=company_id,
            dataset_id=dataset_id,
            execution_id=execution_id,
            language=language,
            prompt_version=prompt_version,
            schema_version=schema_version,
            communication_contract_version=communication_contract_version,
            artifact_version=artifact_version,
            llm_provider=llm_provider,
            llm_model=llm_model,
            model_version=model_version,
            content=content,
            generated_by=generated_by,
            status="draft"
        )
        
        return artifact