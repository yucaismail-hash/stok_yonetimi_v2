# app/decision_intelligence/timeline/ai_artifact_repository.py
"""
AI Artifact Repository - DOCUMENT 06 - PART 03
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class AIArtifactRepository:
    """
    AI Artifact Repository - TL-004
    
    Stores and retrieves all AI Artifacts.
    """
    
    def __init__(self):
        self._artifacts: Dict[str, Dict[str, Any]] = {}
        self._company_artifacts: Dict[str, List[str]] = {}
    
    def save(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Save an AI Artifact."""
        artifact_id = artifact.get("artifact_id", str(uuid4()))
        company_id = artifact.get("company_id")
        
        saved = {
            "artifact_id": artifact_id,
            "artifact_type": artifact.get("artifact_type"),
            "company_id": company_id,
            "execution_id": artifact.get("execution_id"),
            "language": artifact.get("language", "Türkçe"),
            "prompt_version": artifact.get("prompt_version", "1.0.0"),
            "llm_model": artifact.get("llm_model", "unknown"),
            "schema_version": artifact.get("schema_version", "2.0"),
            "structured_content": artifact.get("structured_content", {}),
            "status": artifact.get("status", "active"),
            "created_at": artifact.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
        }
        
        self._artifacts[artifact_id] = saved
        
        if company_id:
            if company_id not in self._company_artifacts:
                self._company_artifacts[company_id] = []
            if artifact_id not in self._company_artifacts[company_id]:
                self._company_artifacts[company_id].append(artifact_id)
        
        logger.info(f"✅ AI Artifact saved: {artifact_id} ({artifact.get('artifact_type')})")
        return saved
    
    def get(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact by ID."""
        return self._artifacts.get(artifact_id)
    
    def get_by_company(self, company_id: str, artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get artifacts by company."""
        artifact_ids = self._company_artifacts.get(company_id, [])
        result = []
        
        for aid in artifact_ids:
            artifact = self.get(aid)
            if artifact:
                if artifact_type and artifact.get("artifact_type") != artifact_type:
                    continue
                result.append(artifact)
        
        return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def get_by_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact by execution ID."""
        for artifact in self._artifacts.values():
            if artifact.get("execution_id") == execution_id:
                return artifact
        return None
    
    def get_latest_analysis_narrative(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get latest analysis narrative for a company."""
        artifacts = self.get_by_company(company_id, "analysis_narrative")
        return artifacts[0] if artifacts else None
    
    def get_latest_timeline(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get latest executive timeline for a company."""
        artifacts = self.get_by_company(company_id, "executive_timeline")
        return artifacts[0] if artifacts else None
    
    def list_artifacts(self, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all artifacts."""
        if company_id:
            return self.get_by_company(company_id)
        return list(self._artifacts.values())