# app/services/ai/mock_provider.py
"""
Mock AI Provider
Fallback when no real AI provider is available.
"""

from typing import Dict, Any, Optional
import json
import logging

from app.services.ai.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class MockProvider(BaseAIProvider):
    """
    Mock AI Provider.
    Sadece geliştirme/test ortamında kullanılır.
    """
    
    def get_default_model(self) -> str:
        return "mock-v1"
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Mock response generation.
        """
        logger.info("🔧 Using Mock AI Provider")
        
        # Basit yanıt üret
        content = f"""
        # AI Decision (MOCK)
        
        ## Summary
        This is a mock AI response. No real AI provider is configured.
        
        ## Analysis
        Based on the provided data, the following observations were made:
        - The forecast shows moderate demand
        - Safety stock levels appear adequate
        - No critical risks identified
        
        ## Recommendations
        1. Review forecast accuracy
        2. Adjust safety stock based on seasonality
        3. Monitor supplier performance
        
        ## Confidence Level
        This is a mock response with 0% confidence.
        """
        
        return {
            "content": content.strip(),
            "model": self.get_default_model(),
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": (len(prompt) + len(content)) // 4,
            },
        }
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Mock JSON response.
        """
        return {
            "status": "mock",
            "message": "Mock AI response",
            "data": {},
            "confidence": 0.0,
        }
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate mock response."""
        return "content" in response