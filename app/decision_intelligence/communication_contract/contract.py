# app/decision_intelligence/communication_contract/contract.py
"""
Communication Contract - DOCUMENT 06 - PART 05
"""

from typing import Dict, Any
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.narrative_payload_builder import NarrativePayloadBuilder
from app.decision_intelligence.communication_contract.prompt_manager import PromptManager
from app.decision_intelligence.communication_contract.narrative_validator import NarrativeValidator

# ✅ Doğru import: app/services/ai/llm_service.py
from app.services.ai.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class CommunicationContract:
    """
    Communication Contract - CP-001
    
    Official communication contract between Stokonomi AI and LLM.
    """
    
    CONTRACT_VERSION = "1.0.0"
    
    def __init__(self):
        self.payload_builder = NarrativePayloadBuilder()
        self.prompt_manager = PromptManager()
        self.llm_service = get_llm_service()
        self.validator = NarrativeValidator()
    
    def execute(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Execute communication contract.
        """
        # 1. Build payload
        payload = self.payload_builder.build(context)
        
        # 2. Build prompt
        prompt_data = self.prompt_manager.build_prompt(context, payload)
        
        # 3. Execute LLM (JSON response)
        response = self.llm_service.generate_json(
            prompt=prompt_data["user_prompt"],
            system_prompt=prompt_data["system_prompt"],
            temperature=0.3,
            max_tokens=1500,
        )
        
        # 4. Add LLM metadata
        metadata = self.llm_service.get_last_response_metadata()
        response["_llm_metadata"] = metadata
        
        # 5. Validate response
        is_valid, errors = self.validator.validate(response, context)
        
        if not is_valid:
            logger.warning(f"⚠️ Validation failed: {errors}")
            response["_validation_errors"] = errors
        
        # 6. Add contract metadata
        response["_contract"] = {
            "contract_version": self.CONTRACT_VERSION,
            "prompt_version": prompt_data["prompt_version"],
            "prompt_type": prompt_data["prompt_type"],
            "validated": is_valid,
        }
        
        return response