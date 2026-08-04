# app/decision_intelligence/advisor/structured_executive_report_builder.py
"""
Structured Executive Report Builder - DOCUMENT 06 - PART 04
"""

from typing import Dict, Any
from datetime import datetime

from app.decision_intelligence.advisor.executive_advisor_context import ExecutiveAdvisorContext


class StructuredExecutiveReportBuilder:
    """
    Structured Executive Report Builder - EA-007
    
    Builds structured JSON executive report.
    """
    
    def build(self, recommendations: Dict[str, Any], context: ExecutiveAdvisorContext) -> Dict[str, Any]:
        """
        Build structured executive report.
        """
        return {
            "schema_version": "1.0",
            "report_type": "executive_advisor",
            "company_id": str(context.company_id),
            "company_name": context.company_name,
            "generated_at": datetime.now().isoformat(),
            "language": context.user_language,
            "sections": {
                "company_health": recommendations.get("company_health", ""),
                "strategic_risks": recommendations.get("strategic_risks", []),
                "strategic_opportunities": recommendations.get("strategic_opportunities", []),
                "management_priorities": recommendations.get("management_priorities", []),
                "long_term_recommendations": recommendations.get("long_term_recommendations", []),
            },
            "explainability": recommendations.get("_explainability", {}),
            "metadata": {
                "is_fallback": recommendations.get("is_fallback", False),
                "timeline_period": context.executive_timeline.get("timeline_period", ""),
                "knowledge_maturity_level": context.knowledge_maturity.get("maturity_level", "unknown"),
                "prompt_version": context.prompt_version,
            },
        }