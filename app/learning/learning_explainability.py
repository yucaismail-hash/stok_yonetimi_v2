# app/learning/learning_explainability.py
"""
Learning Explainability - DOCUMENT 05 - PART 01
Makes every learning update explainable.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from app.learning.learning_context import LearningContext


logger = logging.getLogger(__name__)


class LearningExplainability:
    """
    Learning Explainability - DOCUMENT 05
    
    Records:
    - What changed
    - Why it changed
    - Which execution caused the change
    - Confidence variation
    - Knowledge evolution
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._explanations: List[Dict[str, Any]] = []
    
    def explain(self, context: LearningContext, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanation for learning updates."""
        explanation = {
            "learning_cycle_id": context.learning_cycle_id,
            "execution_id": str(context.execution_id),
            "business_objective": context.business_objective,
            "timestamp": datetime.now().isoformat(),
            "layers": [],
            "summary": "",
            "confidence_changes": [],
        }
        
        # Layer explanations
        if "company_learning" in results.get("layers", {}):
            explanation["layers"].append({
                "layer": "company_learning",
                "changes": self._explain_company_learning(results["layers"]["company_learning"]),
            })
        
        if "pattern_intelligence" in results.get("layers", {}):
            explanation["layers"].append({
                "layer": "pattern_intelligence",
                "changes": self._explain_pattern_intelligence(results["layers"]["pattern_intelligence"]),
            })
        
        if "decision_learning" in results.get("layers", {}):
            explanation["layers"].append({
                "layer": "decision_learning",
                "changes": self._explain_decision_learning(results["layers"]["decision_learning"]),
            })
        
        if "knowledge_maturity" in results.get("layers", {}):
            explanation["layers"].append({
                "layer": "knowledge_maturity",
                "changes": self._explain_knowledge_maturity(results["layers"]["knowledge_maturity"]),
            })
        
        # Summary
        explanation["summary"] = self._generate_summary(explanation)
        
        # Store explanation
        self._explanations.append(explanation)
        
        return explanation
    
    def _explain_company_learning(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explain company learning changes."""
        changes = []
        for rule in result.get("rules", []):
            changes.append({
                "type": "rule",
                "rule_id": rule.get("rule_id"),
                "rule_name": rule.get("rule_name"),
                "confidence": rule.get("confidence_score"),
                "action": "created" if rule.get("is_new") else "updated",
            })
        return changes
    
    def _explain_pattern_intelligence(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explain pattern intelligence changes."""
        changes = []
        for pattern in result.get("patterns", []):
            changes.append({
                "type": "pattern",
                "pattern_type": pattern.get("pattern_type"),
                "product_group": pattern.get("product_group_id"),
                "confidence": pattern.get("confidence_score"),
                "action": "created" if pattern.get("is_new") else "updated",
            })
        return changes
    
    def _explain_decision_learning(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explain decision learning changes."""
        changes = []
        for decision in result.get("decisions", []):
            changes.append({
                "type": "decision",
                "decision_type": decision.get("decision_type"),
                "confidence_before": decision.get("confidence_before"),
                "confidence_after": decision.get("confidence_after"),
                "action": "learned",
            })
        return changes
    
    def _explain_knowledge_maturity(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explain knowledge maturity changes."""
        return [{
            "type": "maturity",
            "level": result.get("maturity_level"),
            "overall_score": result.get("overall_maturity"),
            "action": "calculated",
        }]
    
    def _generate_summary(self, explanation: Dict[str, Any]) -> str:
        """Generate summary of all changes."""
        total_changes = 0
        for layer in explanation.get("layers", []):
            total_changes += len(layer.get("changes", []))
        
        if total_changes == 0:
            return "No changes were made during this learning cycle."
        
        return f"Learning cycle completed with {total_changes} changes across {len(explanation.get('layers', []))} layers."
    
    def get_explanations(self, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all explanations or filter by execution."""
        if execution_id:
            return [e for e in self._explanations if e.get("execution_id") == execution_id]
        return self._explanations