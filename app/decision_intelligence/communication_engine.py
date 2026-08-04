# app/decision_intelligence/communication_engine.py
"""
Communication Engine - DOCUMENT 06 - PART 01
Communicates only through the centralized LLM Service.
"""

from typing import Dict, Any, Optional
import logging

from app.decision_intelligence.decision_context import DecisionContext
from app.decision_intelligence.prompt_manager import PromptManager
from app.services.ai.llm_service import get_llm_service

from app.services.ai.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class CommunicationEngine:
    """
    Communication Engine - DOCUMENT 06
    
    Communicates only through the centralized LLM Service.
    Decision Intelligence NEVER communicates directly with a model provider.
    """
    
    def __init__(self):
        self.prompt_manager = PromptManager()
        self.llm_service = get_llm_service()
    
    def communicate(
        self,
        context: DecisionContext,
        prompt_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Communicate with LLM through centralized service.
        
        Args:
            context: DecisionContext with all results
            prompt_type: Type of prompt to use
        
        Returns:
            LLM response with narrative
        """
        # 1. Build prompt
        prompt_data = self.prompt_manager.build_prompt(context, prompt_type)
        
        # 2. Call LLM service
        try:
            response = self.llm_service.generate_json(
                prompt=prompt_data["user_prompt"],
                system_prompt=prompt_data["system_prompt"],
                temperature=0.3,
                max_tokens=1500,
            )
            
            # 3. Add metadata
            response["_metadata"] = {
                "prompt_type": prompt_type or "executive_summary",
                "prompt_version": context.prompt_version,
                "language": context.user_language,
                "execution_id": str(context.execution_id),
                "generated_at": context.generated_at.isoformat(),
                "model": response.get("model", "unknown"),
            }
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Communication Engine error: {str(e)}")
            return self._get_fallback_response(context, str(e))
    
    def _get_fallback_response(self, context: DecisionContext, error: str) -> Dict[str, Any]:
        """Get fallback response when LLM is unavailable."""
        return {
            "summary": "AI hizmeti şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
            "findings": ["Analiz tamamlandı ancak yorum oluşturulamadı."],
            "risks": ["AI hizmeti kullanılamıyor."],
            "opportunities": [],
            "recommendations": ["Sistemi daha sonra tekrar deneyin."],
            "timeline": "Bekleme",
            "confidence": 0.0,
            "_metadata": {
                "prompt_type": "fallback",
                "prompt_version": context.prompt_version,
                "language": context.user_language,
                "execution_id": str(context.execution_id),
                "generated_at": context.generated_at.isoformat(),
                "error": error,
                "is_fallback": True,
            },
        }