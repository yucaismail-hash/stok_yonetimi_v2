# app/decision_intelligence/narrative_engine/findings_generator.py
"""
Business Findings Generator - DOCUMENT 06 - PART 02
"""

from typing import List, Dict, Any
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.communication_engine import CommunicationEngine

logger = logging.getLogger(__name__)


class FindingsGenerator:
    """
    Business Findings Generator - AN-002
    
    Describes the most important analytical observations.
    Only analytical evidence MAY be used.
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
        self.max_findings = 5
    
    def generate(self, context: DecisionContext) -> List[str]:
        """
        Generate business findings.
        """
        try:
            response = self.communication_engine.communicate(
                context,
                prompt_type="findings",
            )
            
            findings = response.get("findings", [])
            
            # Limit findings
            if len(findings) > self.max_findings:
                findings = findings[:self.max_findings]
            
            return findings
            
        except Exception as e:
            logger.error(f"❌ Findings error: {str(e)}")
            return self._get_fallback_findings(context)
    
    def _get_fallback_findings(self, context: DecisionContext) -> List[str]:
        """Get fallback findings."""
        findings = []
        
        if context.has_forecast():
            forecast = context.forecast_results
            if forecast.get("trend_direction"):
                findings.append(f"Talep trendi: {forecast.get('trend_direction')}")
        
        if context.has_safety_stock():
            ss = context.safety_stock_results
            if ss.get("overall_risk"):
                findings.append(f"Genel risk seviyesi: {ss.get('overall_risk')}")
        
        if context.has_simulation():
            sim = context.simulation_results
            if sim.get("service_level"):
                findings.append(f"Servis seviyesi: %{sim.get('service_level')*100:.1f}")
        
        if not findings:
            findings.append("Analiz tamamlandı.")
        
        return findings