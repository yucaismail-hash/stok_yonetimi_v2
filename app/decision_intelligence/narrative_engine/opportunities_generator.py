# app/decision_intelligence/narrative_engine/opportunities_generator.py
"""
Business Opportunity Generator - DOCUMENT 06 - PART 02
"""

from typing import List, Dict, Any
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.communication_engine import CommunicationEngine

logger = logging.getLogger(__name__)


class OpportunitiesGenerator:
    """
    Business Opportunity Generator - AN-004
    
    Each opportunity includes:
    - Opportunity
    - Expected Benefit
    - Business Value
    - Supporting Evidence
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
        self.max_opportunities = 5
    
    def generate(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """
        Generate business opportunities.
        """
        try:
            response = self.communication_engine.communicate(
                context,
                prompt_type="opportunities",
            )
            
            opportunities = response.get("opportunities", [])
            
            structured_opportunities = []
            for opp in opportunities:
                if isinstance(opp, str):
                    structured_opportunities.append({
                        "opportunity": opp,
                        "benefit": "Beklenen iyileşme",
                        "business_value": "Orta",
                        "evidence": "Analiz sonuçları",
                    })
                else:
                    structured_opportunities.append(opp)
            
            if len(structured_opportunities) > self.max_opportunities:
                structured_opportunities = structured_opportunities[:self.max_opportunities]
            
            return structured_opportunities
            
        except Exception as e:
            logger.error(f"❌ Opportunities error: {str(e)}")
            return self._get_fallback_opportunities(context)
    
    def _get_fallback_opportunities(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get fallback opportunities."""
        opportunities = []
        
        if context.has_backtest():
            backtest = context.backtest_results
            best = backtest.get("best_strategy")
            if best:
                opportunities.append({
                    "opportunity": f"{best} stratejisi ile optimizasyon",
                    "benefit": "Maliyet iyileştirmesi",
                    "business_value": "Yüksek",
                    "evidence": "Backtest sonuçları",
                })
        
        if context.has_forecast():
            forecast = context.forecast_results
            if forecast.get("trend_direction") == "increasing":
                opportunities.append({
                    "opportunity": "Artan talep trendi",
                    "benefit": "Stok seviyelerini optimize etme fırsatı",
                    "business_value": "Orta",
                    "evidence": "Forecast analizi",
                })
        
        if not opportunities:
            opportunities.append({
                "opportunity": "Mevcut stratejileri gözden geçirme",
                "benefit": "Potansiyel iyileştirmeler",
                "business_value": "Orta",
                "evidence": "Genel değerlendirme",
            })
        
        return opportunities