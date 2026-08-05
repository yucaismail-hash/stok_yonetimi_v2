"""
ArtifactValidator - DOCUMENT 06A AA-004
Validation logic for AI Artifacts.

Every AI Artifact SHALL pass validation before persistence.
Validation SHALL verify:
- JSON Schema
- Required Fields
- Prompt Version
- Communication Policy
- Numerical Consistency
- Explainability References
- Metadata Completeness
"""

from typing import Dict, Any, List, Optional, warnings
from app.models.artifact import AIArtifact


class ArtifactValidator:
    """
    Validates AI Artifacts against the standard.
    """
    
    REQUIRED_FIELDS = [
        "artifact_type",
        "company_id",
        "content",
        "generated_by"
    ]
    
    REQUIRED_CONTENT_SECTIONS = [
        "header",
        "business_content",
        "explainability",
        "supporting_evidence",
        "metadata"
    ]
    
    def validate(self, artifact: AIArtifact) -> Dict[str, Any]:
        """
        Validate an AI Artifact.
        
        Returns:
            Dict with:
            - is_valid: bool
            - errors: List[str]
            - warnings: List[str]
        """
        errors = []
        warnings = []
        
        # 1. Required Fields Validation
        self._validate_required_fields(artifact, errors)
        
        # 2. Content Structure Validation
        self._validate_content_structure(artifact, errors)
        
        # 3. JSON Schema Validation
        self._validate_json_schema(artifact, errors)
        
        # 4. Prompt Version Validation
        self._validate_prompt_version(artifact, warnings)
        
        # 5. Metadata Completeness
        self._validate_metadata(artifact, warnings)
        
        # 6. Numerical Consistency
        self._validate_numerical_consistency(artifact, warnings)
        
        # 7. Explainability References
        self._validate_explainability(artifact, warnings)
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_required_fields(self, artifact: AIArtifact, errors: List[str]):
        """Validate required fields."""
        for field in self.REQUIRED_FIELDS:
            if not hasattr(artifact, field) or getattr(artifact, field) is None:
                errors.append(f"Required field '{field}' is missing")
    
    def _validate_content_structure(self, artifact: AIArtifact, errors: List[str]):
        """Validate content has required sections."""
        if not artifact.content:
            errors.append("Content is required")
            return
        
        if not isinstance(artifact.content, dict):
            errors.append("Content must be a JSON object")
            return
        
        for section in self.REQUIRED_CONTENT_SECTIONS:
            if section not in artifact.content:
                errors.append(f"Content missing required section: '{section}'")
    
    def _validate_json_schema(self, artifact: AIArtifact, errors: List[str]):
        """Validate JSON schema of content."""
        # Ensure content has the right structure
        # This would be more detailed with a real JSON schema validator
        content = artifact.content
        if isinstance(content, dict):
            # Header validation
            if "header" in content:
                header = content["header"]
                if not isinstance(header, dict):
                    errors.append("Header must be a JSON object")
                elif "title" not in header:
                    errors.append("Header must contain 'title'")
            
            # Business Content validation
            if "business_content" in content:
                business = content["business_content"]
                if not isinstance(business, dict):
                    errors.append("Business Content must be a JSON object")
                elif "findings" not in business:
                    warnings.append("Business Content missing 'findings' section")
            
            # Explainability validation
            if "explainability" in content:
                explainability = content["explainability"]
                if not isinstance(explainability, dict):
                    errors.append("Explainability must be a JSON object")
                elif "source" not in explainability:
                    errors.append("Explainability must contain 'source'")
                elif "generation_time" not in explainability:
                    warnings.append("Explainability missing 'generation_time'")
                elif "contributing_modules" not in explainability:
                    warnings.append("Explainability missing 'contributing_modules'")
    
    def _validate_prompt_version(self, artifact: AIArtifact, warnings: List[str]):
        """Validate prompt version."""
        if not artifact.prompt_version:
            warnings.append("Prompt version is not set")
    
    def _validate_metadata(self, artifact: AIArtifact, warnings: List[str]):
        """Validate metadata completeness."""
        if not artifact.llm_provider:
            warnings.append("LLM provider is not set")
        if not artifact.llm_model:
            warnings.append("LLM model is not set")
        if not artifact.schema_version:
            warnings.append("Schema version is not set")
    
    def _validate_numerical_consistency(self, artifact: AIArtifact, warnings: List[str]):
        """Validate numerical consistency."""
        # Placeholder - would check numbers in content
        pass
    
    def _validate_explainability(self, artifact: AIArtifact, warnings: List[str]):
        """Validate explainability references."""
        content = artifact.content
        if isinstance(content, dict) and "explainability" in content:
            explainability = content["explainability"]
            if "supporting_evidence" not in explainability:
                warnings.append("Explainability missing 'supporting_evidence' references")