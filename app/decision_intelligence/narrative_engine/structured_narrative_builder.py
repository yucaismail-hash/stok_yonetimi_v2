# app/decision_intelligence/narrative_engine/structured_narrative_builder.py
"""
Structured Narrative Builder - DOCUMENT 06 - PART 02
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.narrative_engine.executive_summary_generator import ExecutiveSummaryGenerator
from app.decision_intelligence.narrative_engine.findings_generator import FindingsGenerator
from app.decision_intelligence.narrative_engine.risks_generator import RisksGenerator
from app.decision_intelligence.narrative_engine.opportunities_generator import OpportunitiesGenerator
from app.decision_intelligence.narrative_engine.recommendations_generator import RecommendationsGenerator
from app.decision_intelligence.narrative_engine.explainability_generator import ExplainabilityGenerator

logger = logging.getLogger(__name__)


class StructuredNarrativeBuilder:
    """
    Structured Narrative Builder - AN-007
    
    Builds complete structured Decision Narrative.
    """
    
    def __init__(self):
        self.executive_summary = ExecutiveSummaryGenerator()
        self.findings = FindingsGenerator()
        self.risks = RisksGenerator()
        self.opportunities = OpportunitiesGenerator()
        self.recommendations = RecommendationsGenerator()
        self.explainability = ExplainabilityGenerator()
    
    def build(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Build complete structured narrative.
        """
        # Generate all components
        summary = self.executive_summary.generate(context)
        findings = self.findings.generate(context)
        risks = self.risks.generate(context)
        opportunities = self.opportunities.generate(context)
        recommendations = self.recommendations.generate(context)
        explainability = self.explainability.generate(context, recommendations)
        
        narrative = {
            "narrative_id": context.narrative_id or "pending",
            "execution_id": str(context.execution_id),
            "workflow_id": context.workflow_id,
            "business_objective": context.business_objective,
            "generated_at": context.generated_at.isoformat(),
            "language": context.user_language,
            "version": context.narrative_version,
            "sections": {
                "executive_summary": summary,
                "business_findings": findings,
                "business_risks": risks,
                "business_opportunities": opportunities,
                "recommended_actions": recommendations,
                "decision_explainability": explainability,
            },
            "metadata": {
                "analyses_available": context.get_available_analyses(),
                "confidence_level": context.get_confidence_level(),
                "is_regeneration": context.is_regeneration,
                "prompt_version": context.prompt_version,
            },
            "structure_version": "2.0",
        }
        
        return narrative
    
    def to_json(self, narrative: Dict[str, Any]) -> str:
        """Convert narrative to JSON string."""
        import json
        return json.dumps(narrative, indent=2, ensure_ascii=False)