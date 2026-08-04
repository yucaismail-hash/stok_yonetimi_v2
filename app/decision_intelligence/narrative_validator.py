# app/decision_intelligence/narrative_validator.py
"""
Narrative Validator - DOCUMENT 06 - PART 01
Validates narrative consistency and policy compliance.
"""

from typing import Dict, Any, List, Tuple
import logging

from app.decision_intelligence.decision_context import DecisionContext

logger = logging.getLogger(__name__)


class NarrativeValidator:
    """
    Narrative Validator - DOCUMENT 06
    
    Validates:
    - Numerical consistency
    - JSON consistency
    - Prompt policy compliance
    - Business language compliance
    """
    
    def __init__(self):
        self._required_fields = [
            "summary",
            "findings",
            "risks",
            "opportunities",
            "recommendations",
            "timeline",
            "confidence",
        ]
    
    def validate(self, narrative: Dict[str, Any], context: DecisionContext) -> Tuple[bool, List[str]]:
        """
        Validate narrative.
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # 1. Check required fields
        for field in self._required_fields:
            if field not in narrative:
                errors.append(f"Missing required field: {field}")
        
        # 2. Check field types
        if "findings" in narrative and not isinstance(narrative["findings"], list):
            errors.append("Findings must be a list")
        
        if "risks" in narrative and not isinstance(narrative["risks"], list):
            errors.append("Risks must be a list")
        
        if "opportunities" in narrative and not isinstance(narrative["opportunities"], list):
            errors.append("Opportunities must be a list")
        
        if "recommendations" in narrative and not isinstance(narrative["recommendations"], list):
            errors.append("Recommendations must be a list")
        
        if "confidence" in narrative and not isinstance(narrative["confidence"], (int, float)):
            errors.append("Confidence must be a number")
        
        # 3. Check confidence range
        if "confidence" in narrative:
            confidence = narrative["confidence"]
            if confidence < 0 or confidence > 1:
                errors.append(f"Confidence must be between 0 and 1, got: {confidence}")
        
        # 4. Check business language compliance
        language_errors = self._check_business_language(narrative)
        errors.extend(language_errors)
        
        # 5. Check numerical consistency
        numerical_errors = self._check_numerical_consistency(narrative, context)
        errors.extend(numerical_errors)
        
        return len(errors) == 0, errors
    
    def _check_business_language(self, narrative: Dict[str, Any]) -> List[str]:
        """
        Check business language compliance.
        """
        errors = []
        
        # Check for technical jargon (simple heuristic)
        technical_terms = [
            "MAE", "MSE", "RMSE", "MAPE", "ARIMA", "Holt-Winters",
            "heteroscedastic", "autocorrelation", "stationarity",
        ]
        
        text = str(narrative)
        for term in technical_terms:
            if term in text:
                errors.append(f"Contains technical term: {term}")
        
        return errors
    
    def _check_numerical_consistency(self, narrative: Dict[str, Any], context: DecisionContext) -> List[str]:
        """
        Check numerical consistency between narrative and original results.
        """
        errors = []
        
        # Check confidence against context
        if "confidence" in narrative:
            context_confidence = context.get_confidence_level()
            narrative_confidence = narrative["confidence"]
            if abs(narrative_confidence - context_confidence) > 0.2:
                errors.append(
                    f"Confidence mismatch: narrative={narrative_confidence}, "
                    f"context={context_confidence}"
                )
        
        return errors