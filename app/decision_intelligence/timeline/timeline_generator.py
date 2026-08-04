# app/decision_intelligence/timeline/timeline_generator.py
"""
Timeline Generator - DOCUMENT 06 - PART 03
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from app.decision_intelligence.timeline.timeline_context import TimelineContext
from app.decision_intelligence.communication_engine import CommunicationEngine
from app.decision_intelligence.timeline.structured_timeline_builder import StructuredTimelineBuilder

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """
    Timeline Generator - TL-003
    
    Generates Executive Timeline from AI Artifacts.
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
        self.structured_builder = StructuredTimelineBuilder()
    
    def generate(self, context: TimelineContext) -> Dict[str, Any]:
        """
        Generate executive timeline.
        """
        # 1. Build timeline prompt
        prompt = self._build_timeline_prompt(context)
        
        # 2. Get response from LLM
        try:
            response = self.communication_engine.communicate(
                context,
                prompt_type="timeline",
            )
            
            # 3. Extract timeline components
            timeline = {
                "timeline_period": context.timeline_period,
                "executive_overview": response.get("summary", ""),
                "major_improvements": response.get("improvements", []),
                "major_risks": response.get("risks", []),
                "trend_summary": response.get("trends", []),
                "recommended_focus": response.get("recommendations", []),
                "timeline_explainability": self._build_explainability(context),
                "generated_at": datetime.now().isoformat(),
            }
            
            return timeline
            
        except Exception as e:
            logger.error(f"❌ Timeline generation error: {str(e)}")
            return self._get_fallback_timeline(context)
    
    def _build_timeline_prompt(self, context: TimelineContext) -> str:
        """Build timeline prompt."""
        return f"""
        You are Stokonomi AI, a senior executive assistant.
        
        Generate an Executive Timeline for {context.company_name}.
        
        Timeline Period: {context.timeline_period}
        
        Historical Narratives Analyzed: {len(context.historical_narratives)}
        
        Learning Evolution: {context.learning_evolution}
        
        Knowledge Maturity: {context.knowledge_maturity}
        
        Generate a timeline summary with:
        1. Executive Overview
        2. Major Improvements
        3. Major Risks
        4. Trend Summary
        5. Recommended Focus Areas
        """
    
    def _build_explainability(self, context: TimelineContext) -> Dict[str, Any]:
        """Build timeline explainability."""
        return {
            "timeline_period": context.timeline_period,
            "narratives_analyzed": len(context.historical_narratives),
            "knowledge_maturity": context.knowledge_maturity.get("maturity_level", "unknown"),
            "generated_at": datetime.now().isoformat(),
        }
    
    def _get_fallback_timeline(self, context: TimelineContext) -> Dict[str, Any]:
        """Get fallback timeline."""
        return {
            "timeline_period": context.timeline_period,
            "executive_overview": f"{context.company_name} için tarihsel analiz özeti oluşturulamadı.",
            "major_improvements": ["Yeterli veri yok"],
            "major_risks": ["Yeterli veri yok"],
            "trend_summary": ["Yeterli veri yok"],
            "recommended_focus": ["Daha fazla analiz yapılması önerilir"],
            "timeline_explainability": self._build_explainability(context),
            "is_fallback": True,
        }