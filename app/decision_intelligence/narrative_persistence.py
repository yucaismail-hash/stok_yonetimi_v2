# app/decision_intelligence/narrative_persistence.py
"""
Narrative Persistence - DOCUMENT 06 - PART 01
Stores and reuses Decision Narratives.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import logging

from app.decision_intelligence.decision_context import DecisionContext

logger = logging.getLogger(__name__)


class NarrativePersistence:
    """
    Narrative Persistence - DOCUMENT 06
    
    Stores and reuses Decision Narratives.
    One analysis generates exactly one narrative.
    Previously stored narratives are always reused.
    """
    
    def __init__(self):
        self._narratives: Dict[str, Dict[str, Any]] = {}
        self._execution_narratives: Dict[str, str] = {}
    
    def save(self, narrative: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """
        Save narrative.
        
        Returns:
            Saved narrative with metadata
        """
        narrative_id = context.narrative_id or str(uuid4())
        
        saved_narrative = {
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
        
        self._narratives[narrative_id] = saved_narrative
        self._execution_narratives[str(context.execution_id)] = narrative_id
        
        logger.info(f"✅ Narrative saved: {narrative_id}")
        
        return saved_narrative
    
    def get_narrative(self, narrative_id: str) -> Optional[Dict[str, Any]]:
        """
        Get narrative by ID.
        """
        return self._narratives.get(narrative_id)
    
    def get_by_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get narrative by execution ID.
        """
        narrative_id = self._execution_narratives.get(execution_id)
        if narrative_id:
            return self.get_narrative(narrative_id)
        return None
    
    def get_by_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get all narratives for a workflow.
        """
        result = []
        for narrative in self._narratives.values():
            if narrative.get("workflow_id") == workflow_id:
                result.append(narrative)
        return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def regenerate(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Regenerate narrative.
        """
        # Mark as regeneration
        context.is_regeneration = True
        context.narrative_version += 1
        
        # Generate new narrative
        from app.decision_intelligence.narrative_generator import NarrativeGenerator
        generator = NarrativeGenerator()
        narrative = generator.generate(context, force_regeneration=True)
        
        logger.info(f"🔄 Narrative regenerated: {context.narrative_id}")
        
        return narrative
    
    def list_narratives(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all narratives.
        """
        return list(self._narratives.values())[-limit:]
    
    def delete_narrative(self, narrative_id: str) -> bool:
        """
        Delete narrative.
        """
        if narrative_id in self._narratives:
            del self._narratives[narrative_id]
            # Also remove from execution mapping
            for exec_id, n_id in list(self._execution_narratives.items()):
                if n_id == narrative_id:
                    del self._execution_narratives[exec_id]
            return True
        return False
    
    def count_narratives(self) -> int:
        """
        Count total narratives.
        """
        return len(self._narratives)