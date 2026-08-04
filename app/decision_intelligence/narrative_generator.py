# app/decision_intelligence/narrative_generator.py
"""
Narrative Generator - DOCUMENT 06 - PART 01
Generates business narratives from deterministic results.
"""

from typing import Dict, Any, Optional
import json
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.communication_engine import CommunicationEngine
from app.decision_intelligence.narrative_validator import NarrativeValidator
from app.decision_intelligence.narrative_persistence import NarrativePersistence

logger = logging.getLogger(__name__)


class NarrativeGenerator:
    """
    Narrative Generator - DOCUMENT 06
    
    Generates business narratives from deterministic results.
    One analysis creates one narrative.
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
        self.validator = NarrativeValidator()
        self.persistence = NarrativePersistence()
    
    def generate(
        self,
        context: DecisionContext,
        force_regeneration: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate decision narrative.
        
        Args:
            context: DecisionContext with all results
            force_regeneration: Force regeneration even if narrative exists
        
        Returns:
            Decision narrative with all components
        """
        # 1. Check if narrative already exists
        if not force_regeneration and context.narrative_id:
            existing = self.persistence.get_narrative(context.narrative_id)
            if existing:
                logger.info(f"✅ Using existing narrative: {context.narrative_id}")
                return existing
        
        # 2. Generate full narrative
        narrative = self._generate_full_narrative(context)
        
        # 3. Validate narrative
        is_valid, errors = self.validator.validate(narrative, context)
        
        if not is_valid:
            logger.warning(f"⚠️ Narrative validation failed: {errors}")
            narrative["_validation_errors"] = errors
        
        # 4. Persist narrative
        persisted = self.persistence.save(narrative, context)
        
        # 5. Add metadata
        narrative["narrative_id"] = persisted.get("narrative_id")
        narrative["version"] = persisted.get("version", 1)
        narrative["persisted_at"] = persisted.get("persisted_at")
        
        return narrative
    
    def _generate_full_narrative(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Generate full narrative with all components.
        """
        narrative = {}
        
        # 1. Executive Summary
        summary_response = self.communication_engine.communicate(
            context,
            prompt_type="executive_summary",
        )
        narrative.update(summary_response)
        
        # 2. Findings
        findings_response = self.communication_engine.communicate(
            context,
            prompt_type="findings",
        )
        narrative["findings"] = findings_response.get("findings", [])
        
        # 3. Risks
        risks_response = self.communication_engine.communicate(
            context,
            prompt_type="risks",
        )
        narrative["risks"] = risks_response.get("risks", [])
        
        # 4. Opportunities
        opportunities_response = self.communication_engine.communicate(
            context,
            prompt_type="opportunities",
        )
        narrative["opportunities"] = opportunities_response.get("opportunities", [])
        
        # 5. Recommendations
        recommendations_response = self.communication_engine.communicate(
            context,
            prompt_type="recommendations",
        )
        narrative["recommendations"] = recommendations_response.get("recommendations", [])
        
        # 6. Timeline
        timeline_response = self.communication_engine.communicate(
            context,
            prompt_type="timeline",
        )
        narrative["timeline"] = timeline_response.get("timeline", "İnceleme gerekiyor")
        
        # 7. Confidence
        narrative["confidence"] = context.get_confidence_level()
        
        # 8. Metadata
        narrative["_metadata"] = {
            "execution_id": str(context.execution_id),
            "business_objective": context.business_objective,
            "generated_at": context.generated_at.isoformat(),
            "narrative_version": context.narrative_version,
            "available_analyses": context.get_available_analyses(),
        }
        
        return narrative