# app/decision_intelligence/advisor/strategic_recommendation_generator.py
"""
Strategic Recommendation Generator - DOCUMENT 06 - PART 04
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from app.decision_intelligence.advisor.executive_advisor_context import ExecutiveAdvisorContext
from app.decision_intelligence.communication_engine import CommunicationEngine

logger = logging.getLogger(__name__)


class StrategicRecommendationGenerator:
    """
    Strategic Recommendation Generator - EA-004
    
    Generates strategic recommendations from Executive Timeline.
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
    
    def generate(self, context: ExecutiveAdvisorContext) -> Dict[str, Any]:
        """
        Generate strategic recommendations.
        """
        try:
            # Build prompt
            prompt = self._build_prompt(context)
            
            # Get response
            response = self.communication_engine.communicate(
                context,
                prompt_type="advisor",
            )
            
            return {
                "company_health": response.get("company_health", ""),
                "strategic_risks": response.get("strategic_risks", []),
                "strategic_opportunities": response.get("strategic_opportunities", []),
                "management_priorities": response.get("management_priorities", []),
                "long_term_recommendations": response.get("long_term_recommendations", []),
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"❌ Strategic Recommendation error: {str(e)}")
            return self._get_fallback_recommendations(context)
    
    def _build_prompt(self, context: ExecutiveAdvisorContext) -> str:
        """Build advisor prompt."""
        timeline = context.executive_timeline
        
        return f"""
        You are Stokonomi AI, a senior strategic advisor to the CEO.
        
        Company: {context.company_name}
        
        Executive Timeline:
        Period: {timeline.get('timeline_period', '')}
        Overview: {timeline.get('executive_overview', '')}
        Improvements: {timeline.get('major_improvements', [])}
        Risks: {timeline.get('major_risks', [])}
        Trends: {timeline.get('trend_summary', [])}
        
        Knowledge Maturity: {context.knowledge_maturity}
        
        Generate strategic recommendations for management.
        Focus on:
        1. Company health assessment
        2. Strategic risks
        3. Strategic opportunities
        4. Management priorities
        5. Long-term recommendations
        """
    
    def _get_fallback_recommendations(self, context: ExecutiveAdvisorContext) -> Dict[str, Any]:
        """Get fallback recommendations."""
        return {
            "company_health": f"{context.company_name} için stratejik değerlendirme oluşturulamadı.",
            "strategic_risks": ["Yeterli stratejik veri yok"],
            "strategic_opportunities": ["Yeterli stratejik veri yok"],
            "management_priorities": ["Öncelikle analiz kapasitesini artırın"],
            "long_term_recommendations": ["Daha fazla tarihsel veri toplanması önerilir"],
            "is_fallback": True,
        }
