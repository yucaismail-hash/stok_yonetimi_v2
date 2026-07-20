# app/services/ai/openai_provider.py

import logging
import time
from typing import Dict, Any, Optional
from openai import OpenAI

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


class OpenAIProvider(BaseAIProvider):
    """OpenAI Provider - OpenAI API ile"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self._api_key = api_key or AIConfig.OPENAI_API_KEY
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self._model = model or "gpt-4o-mini"
        self._timeout = timeout or AIConfig.TIMEOUT
        self._client = OpenAI(api_key=self._api_key, timeout=self._timeout)
        self._max_retries = AIConfig.RETRY
        
        logger.info(f"✅ OpenAI Provider hazır: {self._model}")
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """OpenAI'ye prompt gönderir"""
        start_time = time.time()
        last_error = None
        
        temperature = kwargs.get("temperature", AIConfig.TEMPERATURE)
        max_tokens = kwargs.get("max_tokens", AIConfig.MAX_TOKENS)
        
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.95,
                )
                
                response_time_ms = (time.time() - start_time) * 1000
                
                content = response.choices[0].message.content or ""
                usage = response.usage
                
                return AIResponse(
                    content=content.strip(),
                    provider=self.provider_name,
                    model=self._model,
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                    total_tokens=usage.total_tokens if usage else 0,
                    estimated_cost=self.estimate_cost(
                        usage.prompt_tokens if usage else 0,
                        usage.completion_tokens if usage else 0
                    ),
                    response_time_ms=response_time_ms,
                )
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    raise AIProviderTimeoutError(f"OpenAI timeout: {error_msg}", provider=self.provider_name, original_error=e)
                elif "getaddrinfo" in error_msg.lower() or "connection" in error_msg.lower():
                    raise AIProviderConnectionError(f"OpenAI connection error: {error_msg}", provider=self.provider_name, original_error=e)
                elif "429" in error_msg or "rate" in error_msg.lower() or "quota" in error_msg.lower():
                    raise AIProviderRateLimitError(f"OpenAI rate limit: {error_msg}", provider=self.provider_name, original_error=e)
                elif "404" in error_msg or "not found" in error_msg.lower() or "model" in error_msg.lower():
                    raise AIProviderModelNotFoundError(f"OpenAI model not found: {error_msg}", provider=self.provider_name, original_error=e)
                elif "auth" in error_msg.lower() or "api key" in error_msg.lower() or "invalid" in error_msg.lower():
                    raise AIAuthenticationError(f"OpenAI auth error: {error_msg}", provider=self.provider_name, original_error=e)
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg or "504" in error_msg:
                    raise AIProviderServerError(f"OpenAI server error: {error_msg}", provider=self.provider_name, original_error=e)
                
                logger.warning(f"OpenAI çağrısı başarısız (deneme {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    continue
        
        raise last_error or AIProviderServerError("OpenAI çağrısı başarısız", provider=self.provider_name)
    
    def health_check(self) -> Dict[str, Any]:
        """Sağlık kontrolü"""
        start_time = time.time()
        try:
            models = self._client.models.list()
            available = True
            error = None
            model_accessible = any(m.id == self._model for m in models)
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
        OpenAI maliyet tahmini (USD)
        gpt-4o-mini: ~$0.00015/1K input, $0.0006/1K output
        """
        input_cost = input_tokens / 1000 * 0.00015
        output_cost = output_tokens / 1000 * 0.0006
        return round(input_cost + output_cost, 6)