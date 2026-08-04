# app/decision_intelligence/narrative_engine/narrative_persistence.py
"""
Narrative Persistence - DOCUMENT 06 - PART 02
"""

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class NarrativePersistence:
    """
    Narrative Persistence - AN-008
    
    Stores and retrieves Decision Narratives.
    """
    
    def __init__(self):
        self._narratives: Dict[str, Dict[str, Any]] = {}
        self._execution_map: Dict[str, str] = {}
    
    def save(self, narrative: Dict[str, Any], context) -> Dict[str, Any]:
        """Save narrative."""
        narrative_id = context.narrative_id or str(uuid4())
        
        saved = {
            "narrative_id": narrative_id,
            "execution_id": str(context.execution_id),
            "workflow_id": context.workflow_id,
            "business_objective": context.business_objective,
            "narrative": narrative,
            "version": context.narrative_version,
            "created_at": context.generated_at.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_regeneration": context.is_regeneration,
        }
        
        self._narratives[narrative_id] = saved
        self._execution_map[str(context.execution_id)] = narrative_id
        
        logger.info(f"✅ Narrative saved: {narrative_id}")
        return saved
    
    def get(self, narrative_id: str) -> Optional[Dict[str, Any]]:
        """Get narrative by ID."""
        return self._narratives.get(narrative_id)
    
    def get_by_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get narrative by execution ID."""
        narrative_id = self._execution_map.get(execution_id)
        if narrative_id:
            return self.get(narrative_id)
        return None