# app/decision_intelligence/timeline/timeline_reuse_manager.py
"""
Timeline Reuse Manager - DOCUMENT 06 - PART 03
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.decision_intelligence.timeline.ai_artifact_repository import AIArtifactRepository

logger = logging.getLogger(__name__)


class TimelineReuseManager:
    """
    Timeline Reuse Manager - TL-008
    
    Manages reuse of existing Executive Timelines.
    """
    
    def __init__(self):
        self.repository = AIArtifactRepository()
    
    def should_reuse(self, context) -> bool:
        """Determine if timeline should be reused."""
        return not context.metadata.get("force_regeneration", False)
    
    def get_reusable_timeline(self, context) -> Optional[Dict[str, Any]]:
        """Get reusable timeline if exists."""
        if not self.should_reuse(context):
            return None
        
        # Check if timeline exists for this company
        return self.repository.get_latest_timeline(str(context.company_id))
    
    def mark_as_reused(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Mark timeline as reused."""
        timeline["_reused"] = True
        timeline["_reused_at"] = datetime.now().isoformat()
        return timeline
