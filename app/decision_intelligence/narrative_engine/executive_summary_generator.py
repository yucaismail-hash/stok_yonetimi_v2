# app/decision_intelligence/narrative_engine/executive_summary_generator.py
"""
Executive Summary Generator - DOCUMENT 06 - PART 02
Generates executive summary from DecisionContext.
"""

from typing import Dict, Any
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.communication_engine import CommunicationEngine

logger = logging.getLogger(__name__)


class ExecutiveSummaryGenerator:
    """
    Executive Summary Generator - AN-001
    
    Answers:
    - What happened?
    - Why does it matter?
    - What should management know?
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
        self.max_length = 200  # Configurable
    
    def generate(self, context: DecisionContext) -> str:
        """
        Generate executive summary.
        """
        try:
            response = self.communication_engine.communicate(
                context,
                prompt_type="executive_summary",
            )
            
            summary = response.get("summary", "")
            
            # Truncate if needed
            if len(summary) > self.max_length:
                summary = summary[:self.max_length] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Executive Summary error: {str(e)}")
            return self._get_fallback_summary(context)
    
    def _get_fallback_summary(self, context: DecisionContext) -> str:
        """Get fallback summary."""
        analyses = context.get_available_analyses()
        analyses_text = ", ".join(analyses) if analyses else "analiz"
        return f"{context.business_objective} analizi tamamlandı. {len(analyses)} farklı analiz yöntemi kullanıldı."