# app/decision_intelligence/timeline/timeline_explainability.py
"""
Timeline Explainability - DOCUMENT 06 - PART 03
"""

from typing import Dict, Any, List
from datetime import datetime


class TimelineExplainability:
    """
    Timeline Explainability - TL-006
    
    Explains how timeline was generated.
    """
    
    def explain(self, context, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explainability for timeline.
        """
        return {
            "timeline_period": context.timeline_period,
            "narratives_analyzed": len(context.historical_narratives),
            "learning_evolution": {
                "company_learning": context.learning_evolution.get("company_learning", {}),
                "pattern_intelligence": context.learning_evolution.get("pattern_intelligence", {}),
                "decision_learning": context.learning_evolution.get("decision_learning", {}),
            },
            "knowledge_maturity": context.knowledge_maturity,
            "generated_at": datetime.now().isoformat(),
            "supporting_artifacts": self._list_supporting_artifacts(context),
        }
    
    def _list_supporting_artifacts(self, context) -> List[str]:
        """List supporting AI Artifacts."""
        artifacts = []
        for narrative in context.historical_narratives[:5]:
            artifact_id = narrative.get("artifact_id")
            if artifact_id:
                artifacts.append(artifact_id)
        return artifacts