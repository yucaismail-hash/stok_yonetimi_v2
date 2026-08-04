# app/services/ai/llm_service.py
"""
LLM Servis Katmanı - Gemini (google-genai paketi ile)
Model adı .env'den alınır.

DOCUMENT 06 - Communication Layer entegrasyonu:
- Provider independent
- JSON response desteği
- System prompt desteği
"""

import os
import json
import logging
from typing import Optional, Dict, Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiProvider:
    """Google Gemini Provider"""
    
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
    
    def generate_with_system_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> str:
        """
        System prompt ile Gemini'ye gönderir.
        DOCUMENT 06 - Communication Layer
        """
        full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
        return self.generate(full_prompt, temperature, max_tokens)
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        """
        JSON yanıt bekleyen prompt gönderir.
        DOCUMENT 06 - Structured Narrative
        """
        # JSON format talimatını ekle
        json_instruction = """
        IMPORTANT: Return ONLY valid JSON. No additional text outside the JSON.
        """
        
        full_prompt = prompt + "\n\n" + json_instruction
        
        if system_prompt:
            full_prompt = system_prompt + "\n\n" + full_prompt
        
        try:
            response_text = self.generate(full_prompt, temperature, max_tokens)
            
            # JSON parse et
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse hatası: {e}")
            logger.debug(f"Response: {response_text[:200]}...")
            return {
                "error": "JSON parse failed",
                "raw": response_text[:500],
                "is_fallback": True,
            }
        except Exception as e:
            logger.error(f"❌ Gemini JSON hatası: {e}")
            return {
                "error": str(e),
                "is_fallback": True,
            }


class LLMService:
    """LLM Servisi - Provider independent"""
    
    _providers = {
        "gemini": GeminiProvider,
    }
    
    def __init__(self, provider: str = "gemini", **provider_kwargs):
        if provider not in self._providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        self.provider = self._providers[provider](**provider_kwargs)
        self.provider_name = provider
        self.model_name = self.provider.model_name
        self._last_response_metadata = {}
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Basit generate"""
        return self.provider.generate(prompt, **kwargs)
    
    def generate_with_system_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """System prompt ile generate"""
        return self.provider.generate_with_system_prompt(prompt, system_prompt, **kwargs)
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        """
        JSON response üretir.
        DOCUMENT 06 - Structured Narrative, Executive Timeline, Executive Advisor
        """
        result = self.provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Metadata'yi sakla
        self._last_response_metadata = {
            "model": self.model_name,
            "provider": self.provider_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        return result
    
    def get_last_response_metadata(self) -> Dict[str, Any]:
        """Son yanıt metadata'sını döndürür"""
        return self._last_response_metadata


# ============================================
# SINGLETON INSTANCE
# ============================================

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Singleton LLM servisini döndürür"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(provider="gemini")
    return _llm_service


def get_provider_info() -> Dict[str, Any]:
    """Mevcut provider bilgisini döndürür"""
    service = get_llm_service()
    return {
        "provider": service.provider_name,
        "model": service.model_name,
        "status": "ready",
    }