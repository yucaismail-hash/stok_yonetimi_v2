# app/decision_intelligence/decision_intelligence_engine.py
"""
Decision Intelligence Engine - DOCUMENT 06 - PART 01
Main orchestrator for Decision Intelligence & Communication.
"""

from typing import Dict, Any, Optional,datetime, List
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.narrative_generator import NarrativeGenerator
from app.decision_intelligence.narrative_persistence import NarrativePersistence
from app.decision_intelligence.narrative_validator import NarrativeValidator

logger = logging.getLogger(__name__)


class DecisionIntelligenceEngine:
    """
    Decision Intelligence Engine - DOCUMENT 06
    
    Main orchestrator for Decision Intelligence & Communication.
    """
    
    def __init__(self):
        self.narrative_generator = NarrativeGenerator()
        self.narrative_persistence = NarrativePersistence()
        self.narrative_validator = NarrativeValidator()
    
    def process(
        self,
        context: DecisionContext,
        force_regeneration: bool = False,
    ) -> Dict[str, Any]:
        """
        Process decision intelligence pipeline.
        
        Args:
            context: DecisionContext with all results
            force_regeneration: Force regeneration of narrative
        
        Returns:
            Complete decision intelligence result
        """
        logger.info(f"🧠 Decision Intelligence started: {context.execution_id}")
        
        # 1. Check if narrative exists
        if not force_regeneration:
            existing = self.narrative_persistence.get_by_execution(str(context.execution_id))
            if existing:
                logger.info(f"✅ Using existing narrative for execution: {context.execution_id}")
                return {
                    "status": "reused",
                    "narrative": existing,
                    "metadata": {
                        "execution_id": str(context.execution_id),
                        "reused": True,
                        "timestamp": context.generated_at.isoformat(),
                    },
                }
        
        # 2. Generate narrative
        narrative = self.narrative_generator.generate(context, force_regeneration)
        
        # 3. Validate narrative
        is_valid, errors = self.narrative_validator.validate(narrative, context)
        
        if not is_valid:
            logger.warning(f"⚠️ Narrative validation failed: {errors}")
            narrative["_validation_errors"] = errors
            narrative["_is_valid"] = False
        else:
            narrative["_is_valid"] = True
        
        # 4. Prepare result
        result = {
            "status": "generated" if not force_regeneration else "regenerated",
            "narrative": narrative,
            "validation": {
                "is_valid": is_valid,
                "errors": errors,
            },
            "metadata": {
                "execution_id": str(context.execution_id),
                "workflow_id": context.workflow_id,
                "business_objective": context.business_objective,
                "generated_at": context.generated_at.isoformat(),
                "prompt_version": context.prompt_version,
                "narrative_version": context.narrative_version,
            },
        }
        
        if force_regeneration:
            result["status"] = "regenerated"
            result["metadata"]["regenerated_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ Decision Intelligence completed: {context.execution_id}")
        
        return result
    
    def regenerate(
        self,
        context: DecisionContext,
    ) -> Dict[str, Any]:
        """
        Regenerate narrative for existing context.
        """
        return self.process(context, force_regeneration=True)
    
    def get_narrative(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get narrative by execution ID.
        """
        return self.narrative_persistence.get_by_execution(execution_id)
    
    def get_narrative_by_id(self, narrative_id: str) -> Optional[Dict[str, Any]]:
        """
        Get narrative by narrative ID.
        """
        return self.narrative_persistence.get_narrative(narrative_id)
    
    def list_narratives(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all narratives.
        """
        return self.narrative_persistence.list_narratives(limit)
    
    def validate_narrative(self, narrative: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """
        Validate a narrative independently.
        """
        is_valid, errors = self.narrative_validator.validate(narrative, context)
        return {
            "is_valid": is_valid,
            "errors": errors,
        }