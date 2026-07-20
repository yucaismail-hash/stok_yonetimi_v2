# app/services/ai/gemini_provider.py

import logging
import time
from typing import Dict, Any, Optional

from google import genai
from google.genai import types

from .base_provider import BaseAIProvider, AIResponse
from .ai_exceptions import (
    AIProviderTimeoutError,
    AIProviderConnectionError,
    AIProviderRateLimitError,
    AIProviderModelNotFoundError,
    AIProviderServerError,
    AIAuthenticationError,
)
from .config import AIConfig

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Google Gemini Provider - Yeni google-genai paketi ile"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self._api_key = api_key or AIConfig.GEMINI_API_KEY
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self._model = model or AIConfig.MODEL
        self._timeout = timeout or AIConfig.TIMEOUT
        self._client = genai.Client(api_key=self._api_key)
        
        self._max_retries = AIConfig.RETRY
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Gemini'ye prompt gönderir"""
        start_time = time.time()
        last_error = None
        
        temperature = kwargs.get("temperature", AIConfig.TEMPERATURE)
        max_tokens = kwargs.get("max_tokens", AIConfig.MAX_TOKENS)
        
        for attempt in range(self._max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        top_p=0.95,
                    )
                )
                
                response_time_ms = (time.time() - start_time) * 1000
                
                if response and response.text:
                    # Token tahmini
                    input_tokens = self.estimate_tokens(prompt)
                    output_tokens = self.estimate_tokens(response.text)
                    
                    return AIResponse(
                        content=response.text.strip(),
                        provider=self.provider_name,
                        model=self._model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=input_tokens + output_tokens,
                        estimated_cost=self.estimate_cost(input_tokens, output_tokens),
                        response_time_ms=response_time_ms,
                    )
                else:
                    logger.warning(f"Gemini yanıtı boş (deneme {attempt + 1})")
                    if attempt < self._max_retries - 1:
                        continue
                    raise AIProviderServerError("Gemini yanıtı boş", provider=self.provider_name)
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # Hata sınıflandırması
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    raise AIProviderTimeoutError(f"Gemini timeout: {error_msg}", provider=self.provider_name, original_error=e)
                elif "getaddrinfo" in error_msg.lower() or "connection" in error_msg.lower():
                    raise AIProviderConnectionError(f"Gemini connection error: {error_msg}", provider=self.provider_name, original_error=e)
                elif "429" in error_msg or "quota" in error_msg.lower():
                    raise AIProviderRateLimitError(f"Gemini rate limit: {error_msg}", provider=self.provider_name, original_error=e)
                elif "404" in error_msg or "not found" in error_msg.lower():
                    raise AIProviderModelNotFoundError(f"Gemini model not found: {error_msg}", provider=self.provider_name, original_error=e)
                elif "auth" in error_msg.lower() or "api key" in error_msg.lower() or "invalid" in error_msg.lower():
                    raise AIAuthenticationError(f"Gemini auth error: {error_msg}", provider=self.provider_name, original_error=e)
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg or "504" in error_msg:
                    raise AIProviderServerError(f"Gemini server error: {error_msg}", provider=self.provider_name, original_error=e)
                
                logger.warning(f"Gemini çağrısı başarısız (deneme {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    continue
        
        raise last_error or AIProviderServerError("Gemini çağrısı başarısız", provider=self.provider_name)
    
    def health_check(self) -> Dict[str, Any]:
        """Sağlık kontrolü"""
        start_time = time.time()
        try:
            # Basit bir ping - models listesini al
            models = self._client.models.list()
            available = True
            error = None
            model_accessible = any(m.name == f"models/{self._model}" for m in models)
        except Exception as e:
            available = False
            error = str(e)
            model_accessible = False
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "available": available,
            "model_accessible": model_accessible,
            "response_time_ms": round(response_time_ms, 2),
            "error": error,
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Basit token tahmini (1 token ≈ 4 karakter)"""
        return int(len(text) / 4) + 1
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Gemini maliyet tahmini (USD)
        gemini-3.1-flash-lite: ~$0.0001/1K input, $0.0004/1K output
        """
        input_cost = input_tokens / 1000 * 0.0001
        output_cost = output_tokens / 1000 * 0.0004
        return round(input_cost + output_cost, 6)