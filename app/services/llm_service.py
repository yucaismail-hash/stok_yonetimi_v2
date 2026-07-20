# app/services/llm_service.py - .env'den model oku

"""
LLM Servis Katmanı - Gemini (google-genai paketi ile)
Model adı .env'den alınır.
"""

import os
import logging
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiProvider:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # ✅ .env'den model adını al, yoksa varsayılan kullan
        self.model_name = model or os.getenv("AI_MODEL", "gemini-2.5-flash")
        
        self.client = genai.Client(api_key=self.api_key)
        self.max_retries = 3
        
        logger.info(f"🤖 AI Model başlatıldı: {self.model_name}")
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500) -> str:
        """Gemini'ye prompt gönderir ve yanıtı döndürür"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        top_p=0.95,
                    )
                )
                
                if response and response.text:
                    return response.text.strip()
                else:
                    logger.warning(f"Gemini yanıtı boş (deneme {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        continue
                    return ""
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini çağrısı başarısız (deneme {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    continue
                raise
        
        raise last_error or Exception("Gemini çağrısı başarısız")


class LLMService:
    _providers = {
        "gemini": GeminiProvider,
    }
    
    def __init__(self, provider: str = "gemini", **provider_kwargs):
        if provider not in self._providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        self.provider = self._providers[provider](**provider_kwargs)
        self.provider_name = provider
        self.model_name = self.provider.model_name
    
    def generate(self, prompt: str, **kwargs) -> str:
        return self.provider.generate(prompt, **kwargs)


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Singleton LLM servisini döndürür"""
    global _llm_service
    if _llm_service is None:
        # ✅ .env'den otomatik okuyacak
        _llm_service = LLMService(provider="gemini")
    return _llm_service