# app/services/ai/llm_service.py

import logging
from typing import Optional, Dict, Any

from .base_provider import AIResponse
from .provider_manager import get_provider_manager
from .ai_exceptions import AIProviderError
from .config import AIConfig

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM Service - TEK GİRİŞ NOKTASI
    
    Sistemde hiçbir yerde doğrudan provider çağrılmaz.
    Tüm AI istekleri buradan yapılır.
    """
    
    def __init__(self):
        self.manager = get_provider_manager()
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """
        Prompt gönderir ve AIResponse döndürür.
        
        Args:
            prompt: Gönderilecek prompt
            **kwargs: temperature, max_tokens, etc.
        
        Returns:
            AIResponse: AI yanıtı
        """
        return self.manager.generate(prompt, **kwargs)
    
    def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prompt gönderir ve JSON yanıtı döndürür.
        """
        response = self.generate(prompt, **kwargs)
        
        # JSON parse et
        import json
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise AIProviderError(f"JSON parse hatası: {e}", provider=response.provider)
    
    def get_stats(self) -> Dict[str, Any]:
        """Provider istatistiklerini döndürür"""
        return self.manager.get_stats()
    
    def health_check(self) -> Dict[str, Any]:
        """Tüm provider'ların sağlık durumunu kontrol eder"""
        return self.manager.health_check_all()
    
    def get_active_provider(self) -> str:
        """Aktif provider adını döndürür"""
        provider = self.manager.get_active_provider()
        return provider.provider_name if provider else "unknown"
    
    def get_provider_info(self) -> Dict[str, str]:
        """✅ Provider ve model bilgilerini birlikte döndürür"""
        provider = self.manager.get_active_provider()
        if provider:
            return {
                "provider": provider.provider_name,
                "model": provider.model_name,
                "version": f"{provider.provider_name}-{provider.model_name}-v1"
            }
        return {
            "provider": "unknown",
            "model": "unknown",
            "version": "unknown"
        }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Singleton LLM Service döndürür"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service