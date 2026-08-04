# app/decision_intelligence/narrative_engine/explainability_generator.py
"""
Decision Explainability Generator - DOCUMENT 06 - PART 02
"""

from typing import Dict, Any, List
import logging

from app.decision_intelligence.decision_context import DecisionContext

logger = logging.getLogger(__name__)


class ExplainabilityGenerator:
    """
    Decision Explainability Generator - AN-006
    
    Identifies which analytical modules contributed to each recommendation.
    """
    
    def generate(self, context: DecisionContext, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate decision explainability.
        """
        modules = {
            "forecast": context.has_forecast(),
            "safety_stock": context.has_safety_stock(),
            "simulation": context.has_simulation(),
            "backtest": context.has_backtest(),
            "supplier": context.has_supplier(),
            "company_learning": bool(context.company_learning),
            "pattern_intelligence": bool(context.pattern_intelligence),
            "decision_learning": bool(context.decision_learning),
        }
        
        # Map recommendations to modules
        recommendation_modules = []
        for rec in recommendations:
            rec_modules = self._map_recommendation_to_modules(rec, modules)
            recommendation_modules.append({
                "recommendation": rec.get("action", rec.get("recommendation", "")),
                "modules": rec_modules,
            })
        
        return {
            "modules_used": [k for k, v in modules.items() if v],
            "module_count": sum(1 for v in modules.values() if v),
            "recommendation_modules": recommendation_modules,
            "confidence": context.get_confidence_level(),
            "knowledge_maturity": context.knowledge_maturity.get("maturity_level", "unknown")
            if context.knowledge_maturity else "unknown",
        }
    
    def _map_recommendation_to_modules(self, recommendation: Dict[str, Any], modules: Dict[str, bool]) -> List[str]:
        """Map a recommendation to contributing modules."""
        mapped = []
        
        text = str(recommendation).lower()
        
        if modules.get("forecast") and any(word in text for word in ["talep", "forecast", "tahmin"]):
            mapped.append("forecast")
        
        if modules.get("safety_stock") and any(word in text for word in ["stoğu", "safety", "emniyet", "stok"]):
            mapped.append("safety_stock")
        
        if modules.get("simulation") and any(word in text for word in ["simülasyon", "simulation", "risk"]):
            mapped.append("simulation")
        
        if modules.get("backtest") and any(word in text for word in ["backtest", "test", "strateji"]):
            mapped.append("backtest")
        
        if modules.get("supplier") and any(word in text for word in ["tedarikçi", "supplier"]):
            mapped.append("supplier")
        
        if modules.get("company_learning") and any(word in text for word in ["şirket", "company", "öğren"]):
            mapped.append("company_learning")
        
        if not mapped:
            mapped = ["general_analysis"]
        
        return mapped