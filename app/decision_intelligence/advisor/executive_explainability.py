# app/decision_intelligence/advisor/executive_explainability.py
"""
Executive Explainability - DOCUMENT 06 - PART 04
"""

from typing import Dict, Any
from datetime import datetime

from app.decision_intelligence.advisor.executive_advisor_context import ExecutiveAdvisorContext


class ExecutiveExplainability:
    """
    Executive Explainability - EA-005
    
    Explains how strategic recommendations were generated.
    """
    
    def explain(self, context: ExecutiveAdvisorContext, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explainability for advisor report.
        """
        return {
            "timeline_used": {
                "period": context.executive_timeline.get("timeline_period", ""),
                "generated_at": context.executive_timeline.get("generated_at", ""),
            },
            "knowledge_maturity": {
                "level": context.knowledge_maturity.get("maturity_level", "unknown"),
                "score": context.knowledge_maturity.get("overall_maturity", 0),
            },
            "historical_reports_analyzed": len(context.historical_reports),
            "prompt_version": context.prompt_version,
            "generated_at": datetime.now().isoformat(),
            "is_fallback": recommendations.get("is_fallback", False),
        }