# app/decision_intelligence/communication_contract/narrative_validator.py
"""
Narrative Validator - DOCUMENT 06 - PART 05
"""

from typing import Dict, Any, List, Tuple
import json
import logging

from app.decision_intelligence.narrative_validator import NarrativeValidator as BaseNarrativeValidator
from app.decision_intelligence.narrative_persistence import NarrativePersistence

from app.services.ai.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class NarrativeValidator:
    """
    Narrative Validator - CP-006
    
    Validates narrative against communication policy.
    """
    
    def __init__(self):        
        self.llm_service = get_llm_service()
        self.validator = BaseNarrativeValidator()
        self.persistence = NarrativePersistence()
        
        self._required_fields = [
            "summary",
            "findings",
            "risks",
            "opportunities",
            "recommendations",
        ]
    
    def validate(self, narrative: Dict[str, Any], context) -> Tuple[bool, List[str]]:
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
        list_fields = ["findings", "risks", "opportunities", "recommendations"]
        for field in list_fields:
            if field in narrative and not isinstance(narrative[field], list):
                errors.append(f"Field '{field}' must be a list")
        
        # 3. Check confidence
        if "confidence" in narrative:
            confidence = narrative["confidence"]
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                errors.append(f"Confidence must be between 0 and 1, got: {confidence}")
        
        # 4. Check policy compliance
        policy_errors = self._check_policy_compliance(narrative)
        errors.extend(policy_errors)
        
        # 5. Check version compatibility
        version_info = self.versioning.get_version_info(narrative)
        if not self.versioning.is_compatible(version_info):
            errors.append(f"Incompatible schema version: {version_info.get('schema_version')}")
        
        return len(errors) == 0, errors
    
    def _check_policy_compliance(self, narrative: Dict[str, Any]) -> List[str]:
        """Check policy compliance."""
        errors = []
        
        # Check for prohibited behaviors
        text = json.dumps(narrative, ensure_ascii=False).lower()
        
        # Check for calculations
        calculation_keywords = ["calculate", "comput", "estimated", "predicted", "forecasted"]
        for keyword in calculation_keywords:
            if keyword in text:
                errors.append(f"Contains prohibited calculation term: {keyword}")
        
        # Check for unsupported conclusions
        if "estimated" in text and not narrative.get("_metadata", {}).get("is_estimation_allowed"):
            errors.append("Contains unsupported estimation")
        
        return errors
