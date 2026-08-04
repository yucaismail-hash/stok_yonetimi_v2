# app/decision_intelligence/narrative_payload_builder.py
"""
Narrative Payload Builder - DOCUMENT 06 - PART 01
Converts deterministic results into standardized JSON payload.
LLM NEVER receives raw execution objects.
"""

from typing import Dict, Any, List, Optional
import json
import logging

from app.decision_intelligence.decision_context import DecisionContext

logger = logging.getLogger(__name__)


class NarrativePayloadBuilder:
    """
    Narrative Payload Builder - DOCUMENT 06
    
    Converts deterministic results into standardized JSON payload.
    Only this payload SHALL be passed to the Prompt Manager.
    """
    
    def __init__(self):
        self._max_items = 10  # Max items to include in payload
    
    def build(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Build standardized JSON payload from context.
        """
        payload = {
            "metadata": {
                "execution_id": str(context.execution_id),
                "workflow_id": context.workflow_id,
                "business_objective": context.business_objective,
                "generated_at": context.generated_at.isoformat(),
                "prompt_version": context.prompt_version,
                "language": context.user_language,
            },
            "company": {
                "name": context.company_name,
                "sector": str(context.sector_id) if context.sector_id else None,
            },
            "results": {},
            "learning": {},
            "scores": {},
            "summary": {},
        }
        
        # Add forecast results
        if context.has_forecast():
            payload["results"]["forecast"] = self._build_forecast_payload(context.forecast_results)
        
        # Add safety stock results
        if context.has_safety_stock():
            payload["results"]["safety_stock"] = self._build_safety_stock_payload(context.safety_stock_results)
        
        # Add simulation results
        if context.has_simulation():
            payload["results"]["simulation"] = self._build_simulation_payload(context.simulation_results)
        
        # Add backtest results
        if context.has_backtest():
            payload["results"]["backtest"] = self._build_backtest_payload(context.backtest_results)
        
        # Add supplier results
        if context.has_supplier():
            payload["results"]["supplier"] = self._build_supplier_payload(context.supplier_results)
        
        # Add learning results
        if context.has_learning():
            payload["learning"] = self._build_learning_payload(context)
        
        # Add decision scores
        if context.decision_scores:
            payload["scores"] = context.decision_scores
        
        # Build summary
        payload["summary"] = self._build_summary(payload)
        
        return payload
    
    def _build_forecast_payload(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build forecast payload."""
        payload = {
            "type": "forecast",
            "total_items": results.get("total", 0),
            "model_used": results.get("model_used", "auto"),
            "accuracy": {
                "mape": results.get("mape"),
                "r2": results.get("r2_score"),
            },
            "trend": results.get("trend_direction"),
            "summary": results.get("summary", "Forecast analysis completed."),
        }
        
        # Add top items if available
        items = results.get("results", [])
        if items:
            payload["items"] = items[:self._max_items]
            payload["items_count"] = len(items)
        
        return payload
    
    def _build_safety_stock_payload(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build safety stock payload."""
        payload = {
            "type": "safety_stock",
            "total_items": results.get("total", 0),
            "service_level": results.get("service_level", 0.95),
            "risk_level": results.get("overall_risk", "Medium"),
            "summary": results.get("summary", "Safety stock analysis completed."),
        }
        
        # Add critical items
        items = results.get("results", [])
        if items:
            critical = [i for i in items if i.get("risk_score", 0) > 0.5]
            payload["critical_items"] = critical[:self._max_items]
            payload["critical_count"] = len(critical)
        
        return payload
    
    def _build_simulation_payload(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build simulation payload."""
        return {
            "type": "simulation",
            "total_items": results.get("total", 0),
            "num_simulations": results.get("num_simulations", 1000),
            "service_level": results.get("service_level"),
            "tail_risk": results.get("tail_risk"),
            "summary": results.get("summary", "Simulation analysis completed."),
        }
    
    def _build_backtest_payload(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build backtest payload."""
        payload = {
            "type": "backtest",
            "total_items": results.get("total", 0),
            "best_strategy": results.get("best_strategy", "hybrid"),
            "service_level": results.get("service_level"),
            "total_cost": results.get("total_cost"),
            "summary": results.get("summary", "Backtest analysis completed."),
        }
        
        # Add strategy comparison
        comparison = results.get("comparison", {})
        if comparison:
            payload["comparison"] = {
                "best": comparison.get("best"),
                "worst": comparison.get("worst"),
                "strategies_tested": len(comparison),
            }
        
        return payload
    
    def _build_supplier_payload(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build supplier payload."""
        payload = {
            "type": "supplier",
            "total_items": results.get("total", 0),
            "high_risk_count": results.get("high_risk_count", 0),
            "avg_risk_score": results.get("avg_risk_score"),
            "summary": results.get("summary", "Supplier analysis completed."),
        }
        
        # Add top suppliers
        suppliers = results.get("suppliers", [])
        if suppliers:
            payload["top_suppliers"] = suppliers[:self._max_items]
        
        return payload
    
    def _build_learning_payload(self, context: DecisionContext) -> Dict[str, Any]:
        """Build learning payload."""
        payload = {
            "company_learning": {
                "confidence": context.company_learning.get("confidence", 0.5),
                "profile": context.company_learning.get("profile", {}),
            },
            "pattern_intelligence": {
                "patterns": context.pattern_intelligence.get("total_skus", 0),
                "confidence": context.pattern_intelligence.get("confidence", 0.5),
            },
            "decision_learning": {
                "scores": context.decision_scores,
                "confidence": context.decision_learning.get("confidence", 0.5),
            },
            "knowledge_maturity": {
                "level": context.knowledge_maturity.get("maturity_level", "initial"),
                "overall": context.knowledge_maturity.get("overall_maturity", 0),
                "health": context.knowledge_maturity.get("overall_health", {}),
            },
        }
        
        return payload
    
    def _build_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build summary of all results."""
        results = payload.get("results", {})
        
        summary = {
            "total_analyses": len(results),
            "analysis_types": list(results.keys()),
            "has_forecast": "forecast" in results,
            "has_safety_stock": "safety_stock" in results,
            "has_simulation": "simulation" in results,
            "has_backtest": "backtest" in results,
            "has_supplier": "supplier" in results,
            "learning_available": bool(payload.get("learning")),
        }
        
        # Determine primary result type
        if "forecast" in results:
            summary["primary_analysis"] = "forecast"
        elif "safety_stock" in results:
            summary["primary_analysis"] = "safety_stock"
        elif "simulation" in results:
            summary["primary_analysis"] = "simulation"
        else:
            summary["primary_analysis"] = "unknown"
        
        return summary