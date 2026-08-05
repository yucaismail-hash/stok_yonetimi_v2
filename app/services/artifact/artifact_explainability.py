"""
ArtifactExplainability - DOCUMENT 06A AA-007
Explainability management for AI Artifacts.

Every AI Artifact SHALL explain:
- Its source
- Its generation time
- Its contributing analytical modules
- Its supporting evidence

Explainability SHALL remain machine-readable.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from app.models.artifact import AIArtifact


class ArtifactExplainability:
    """
    Manages explainability for AI Artifacts.
    """
    
    def build_explainability(
        self,
        source: str,
        generation_time: datetime,
        contributing_modules: List[str],
        supporting_evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build an explainability object.
        """
        return {
            "source": source,
            "generation_time": generation_time.isoformat() if generation_time else None,
            "contributing_modules": contributing_modules,
            "supporting_evidence": supporting_evidence
        }
    
    def add_explainability_to_artifact(
        self,
        artifact: AIArtifact,
        source: str,
        contributing_modules: List[str],
        supporting_evidence: List[Dict[str, Any]]
    ) -> AIArtifact:
        """
        Add explainability to an artifact's content.
        """
        if not artifact.content:
            artifact.content = {}
        
        if not isinstance(artifact.content, dict):
            artifact.content = {}
        
        artifact.content["explainability"] = self.build_explainability(
            source=source,
            generation_time=datetime.utcnow(),
            contributing_modules=contributing_modules,
            supporting_evidence=supporting_evidence
        )
        
        return artifact
    
    def get_explainability(self, artifact: AIArtifact) -> Optional[Dict[str, Any]]:
        """
        Get explainability from an artifact's content.
        """
        if not artifact.content:
            return None
        
        if not isinstance(artifact.content, dict):
            return None
        
        return artifact.content.get("explainability")
    
    def get_source(self, artifact: AIArtifact) -> Optional[str]:
        """Get the source of an artifact."""
        explainability = self.get_explainability(artifact)
        if explainability:
            return explainability.get("source")
        return None
    
    def get_contributing_modules(self, artifact: AIArtifact) -> List[str]:
        """Get contributing modules of an artifact."""
        explainability = self.get_explainability(artifact)
        if explainability:
            return explainability.get("contributing_modules", [])
        return []