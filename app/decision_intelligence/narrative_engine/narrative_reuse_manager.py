# app/decision_intelligence/narrative_engine/narrative_reuse_manager.py
"""
Narrative Reuse Manager - DOCUMENT 06 - PART 02
"""

from typing import Optional, Dict, Any, datetime
import logging

logger = logging.getLogger(__name__)


class NarrativeReuseManager:
    """
    Narrative Reuse Manager - AN-009
    
    Manages reuse of existing narratives.
    """
    
    def __init__(self, persistence):
        self.persistence = persistence
    
    def should_reuse(self, context) -> bool:
        """Determine if narrative should be reused."""
        # Always reuse unless regeneration requested
        return not context.is_regeneration
    
    def get_reusable_narrative(self, context) -> Optional[Dict[str, Any]]:
        """Get reusable narrative if exists."""
        if not self.should_reuse(context):
            return None
        
        return self.persistence.get_by_execution(str(context.execution_id))
    
    def mark_for_reuse(self, narrative: Dict[str, Any]) -> Dict[str, Any]:
        """Mark narrative as reused."""
        narrative["_reused"] = True
        narrative["_reused_at"] = datetime.now().isoformat()
        return narrative