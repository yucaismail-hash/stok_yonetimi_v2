# app/decision_intelligence/timeline/structured_timeline_builder.py
"""
Structured Timeline Builder - DOCUMENT 06 - PART 03
"""

from typing import Dict, Any
from datetime import datetime


class StructuredTimelineBuilder:
    """
    Structured Timeline Builder - TL-009
    
    Builds structured JSON timeline.
    """
    
    def build(self, timeline: Dict[str, Any], context) -> Dict[str, Any]:
        """
        Build structured timeline.
        """
        return {
            "schema_version": "2.0",
            "timeline_period": context.timeline_period,
            "company_id": str(context.company_id),
            "company_name": context.company_name,
            "generated_at": datetime.now().isoformat(),
            "language": context.user_language,
            "sections": {
                "executive_overview": timeline.get("executive_overview", ""),
                "major_improvements": timeline.get("major_improvements", []),
                "major_risks": timeline.get("major_risks", []),
                "trend_summary": timeline.get("trend_summary", []),
                "recommended_focus": timeline.get("recommended_focus", []),
            },
            "explainability": timeline.get("timeline_explainability", {}),
            "metadata": {
                "is_fallback": timeline.get("is_fallback", False),
                "narratives_analyzed": len(context.historical_narratives),
                "knowledge_maturity": context.knowledge_maturity.get("maturity_level", "unknown"),
                "prompt_version": context.prompt_version,
            },
        }