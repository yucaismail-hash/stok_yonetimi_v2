# app/decision_intelligence/narrative_engine/risks_generator.py
"""
Business Risk Generator - DOCUMENT 06 - PART 02
"""

from typing import List, Dict, Any
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.communication_engine import CommunicationEngine

logger = logging.getLogger(__name__)


class RisksGenerator:
    """
    Business Risk Generator - AN-003
    
    Each risk includes:
    - Risk
    - Business Impact
    - Analytical Evidence
    - Priority
    """
    
    def __init__(self):
        self.communication_engine = CommunicationEngine()
        self.max_risks = 5
    
    def generate(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """
        Generate business risks.
        """
        try:
            response = self.communication_engine.communicate(
                context,
                prompt_type="risks",
            )
            
            risks = response.get("risks", [])
            
            # Convert to structured format if plain strings
            structured_risks = []
            for risk in risks:
                if isinstance(risk, str):
                    structured_risks.append({
                        "risk": risk,
                        "impact": "Belirsiz",
                        "evidence": "Analiz sonuçları",
                        "priority": "Orta",
                    })
                else:
                    structured_risks.append(risk)
            
            if len(structured_risks) > self.max_risks:
                structured_risks = structured_risks[:self.max_risks]
            
            return structured_risks
            
        except Exception as e:
            logger.error(f"❌ Risks error: {str(e)}")
            return self._get_fallback_risks(context)
    
    def _get_fallback_risks(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get fallback risks."""
        risks = []
        
        if context.has_simulation():
            sim = context.simulation_results
            if sim.get("tail_risk", 0) > 0.5:
                risks.append({
                    "risk": "Stok tükenme riski yüksek",
                    "impact": "Müşteri memnuniyeti ve satış kaybı",
                    "evidence": "Simülasyon sonuçları",
                    "priority": "Yüksek",
                })
        
        if context.has_safety_stock():
            ss = context.safety_stock_results
            if ss.get("overall_risk") == "High":
                risks.append({
                    "risk": "Emniyet stoğu yetersiz",
                    "impact": "Stok tükenmesi ve acil sipariş maliyetleri",
                    "evidence": "Safety Stock analizi",
                    "priority": "Yüksek",
                })
        
        if not risks:
            risks.append({
                "risk": "Belirgin risk tespit edilmedi",
                "impact": "Normal operasyonel riskler mevcut",
                "evidence": "Genel değerlendirme",
                "priority": "Düşük",
            })
        
        return risks