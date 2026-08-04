# app/decision_intelligence/narrative_engine/recommendations_generator.py
"""
Recommendation Generator - DOCUMENT 06 - PART 02
"""

from typing import List, Dict, Any
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.communication_engine import CommunicationEngine

logger = logging.getLogger(__name__)


class RecommendationsGenerator:
    """
    Recommendation Generator - AN-005
    
    Each recommendation contains:
    - Recommended Action
    - Reason
    - Expected Benefit
    - Supporting Evidence
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
        self.max_recommendations = 5
    
    def generate(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """
        Generate recommendations.
        """
        try:
            response = self.communication_engine.communicate(
                context,
                prompt_type="recommendations",
            )
            
            recommendations = response.get("recommendations", [])
            
            structured = []
            for rec in recommendations:
                if isinstance(rec, str):
                    structured.append({
                        "action": rec,
                        "reason": "Analiz sonuçlarına dayanarak",
                        "benefit": "Beklenen iyileşme",
                        "evidence": "Analiz sonuçları",
                    })
                else:
                    structured.append(rec)
            
            if len(structured) > self.max_recommendations:
                structured = structured[:self.max_recommendations]
            
            return structured
            
        except Exception as e:
            logger.error(f"❌ Recommendations error: {str(e)}")
            return self._get_fallback_recommendations(context)
    
    def _get_fallback_recommendations(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get fallback recommendations."""
        recommendations = []
        
        if context.has_safety_stock():
            ss = context.safety_stock_results
            if ss.get("overall_risk") in ["High", "Medium"]:
                recommendations.append({
                    "action": "Emniyet stoğu seviyelerini gözden geçirin",
                    "reason": "Mevcut risk seviyesi yüksek",
                    "benefit": "Stok tükenme riskini azaltır",
                    "evidence": "Safety Stock analizi",
                })
        
        if context.has_simulation():
            sim = context.simulation_results
            if sim.get("tail_risk", 0) > 0.4:
                recommendations.append({
                    "action": "Talep değişkenliğini yakından izleyin",
                    "reason": "Tail risk yüksek",
                    "benefit": "Sürpriz stok tükenmelerini önler",
                    "evidence": "Simülasyon sonuçları",
                })
        
        if not recommendations:
            recommendations.append({
                "action": "Mevcut stratejileri koruyun",
                "reason": "Belirgin risk veya fırsat tespit edilmedi",
                "benefit": "İstikrarlı operasyon",
                "evidence": "Genel değerlendirme",
            })
        
        return recommendations