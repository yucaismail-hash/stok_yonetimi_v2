# app/decision_intelligence/timeline/timeline_persistence.py
"""
Timeline Persistence - DOCUMENT 06 - PART 03
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.decision_intelligence.timeline.ai_artifact_repository import AIArtifactRepository
from app.decision_intelligence.timeline.ai_artifact_serializer import AIArtifactSerializer

logger = logging.getLogger(__name__)


class TimelinePersistence:
    """
    Timeline Persistence - TL-007
    
    Persists and retrieves Executive Timelines as AI Artifacts.
    """
    
    def __init__(self):
        self.repository = AIArtifactRepository()
        self.serializer = AIArtifactSerializer()
    
    def save(self, timeline: Dict[str, Any], context) -> Dict[str, Any]:
        """Save timeline as AI Artifact."""
        artifact = self.serializer.create_artifact(
            artifact_type="executive_timeline",
            company_id=str(context.company_id),
            execution_id=context.metadata.get("execution_id", ""),
            structured_content=timeline,
            metadata={
                "timeline_period": context.timeline_period,
                "language": context.user_language,
                "prompt_version": context.prompt_version,
                "narratives_analyzed": len(context.historical_narratives),
            },
        )
        
        return self.repository.save(artifact)
    
    def get_latest(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get latest timeline for a company."""
        return self.repository.get_latest_timeline(company_id)
    
    def get_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get timeline by artifact ID."""
        return self.repository.get(artifact_id)