# app/services/ai/deepseek_provider.py

import logging
import time
from typing import Dict, Any, Optional
import httpx

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


class DeepSeekProvider(BaseAIProvider):
    """DeepSeek Provider - DeepSeek API ile"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self._api_key = api_key or AIConfig.DEEPSEEK_API_KEY
        if not self._api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        
        self._model = model or "deepseek-chat"
        self._timeout = timeout or AIConfig.TIMEOUT
        self._base_url = "https://api.deepseek.com/v1"
        self._max_retries = AIConfig.RETRY
        
        logger.info(f"✅ DeepSeek Provider hazır: {self._model}")
    
    @property
    def provider_name(self) -> str:
        return "deepseek"
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """DeepSeek'e prompt gönderir"""
        start_time = time.time()
        last_error = None
        
        temperature = kwargs.get("temperature", AIConfig.TEMPERATURE)
        max_tokens = kwargs.get("max_tokens", AIConfig.MAX_TOKENS)
        
        for attempt in range(self._max_retries):
            try:
                response = self._call_api(prompt, temperature, max_tokens)
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Token bilgilerini çıkar
                usage = response.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return AIResponse(
                    content=content.strip(),
                    provider=self.provider_name,
                    model=self._model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    estimated_cost=self.estimate_cost(input_tokens, output_tokens),
                    response_time_ms=response_time_ms,
                )
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # Hata sınıflandırması
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    raise AIProviderTimeoutError(f"DeepSeek timeout: {error_msg}", provider=self.provider_name, original_error=e)
                elif "getaddrinfo" in error_msg.lower() or "connection" in error_msg.lower():
                    raise AIProviderConnectionError(f"DeepSeek connection error: {error_msg}", provider=self.provider_name, original_error=e)
                elif "429" in error_msg or "quota" in error_msg.lower():
                    raise AIProviderRateLimitError(f"DeepSeek rate limit: {error_msg}", provider=self.provider_name, original_error=e)
                elif "404" in error_msg or "not found" in error_msg.lower():
                    raise AIProviderModelNotFoundError(f"DeepSeek model not found: {error_msg}", provider=self.provider_name, original_error=e)
                elif "auth" in error_msg.lower() or "api key" in error_msg.lower() or "invalid" in error_msg.lower():
                    raise AIAuthenticationError(f"DeepSeek auth error: {error_msg}", provider=self.provider_name, original_error=e)
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg or "504" in error_msg:
                    raise AIProviderServerError(f"DeepSeek server error: {error_msg}", provider=self.provider_name, original_error=e)
                
                logger.warning(f"DeepSeek çağrısı başarısız (deneme {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    continue
        
        raise last_error or AIProviderServerError("DeepSeek çağrısı başarısız", provider=self.provider_name)
    
    def _call_api(self, prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """DeepSeek API'yi çağırır"""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": self._model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
        }
        
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Sağlık kontrolü"""
        start_time = time.time()
        try:
            # Basit bir ping - models listesini al
            headers = {"Authorization": f"Bearer {self._api_key}"}
            
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{self._base_url}/models",
                    headers=headers
                )
                available = response.status_code == 200
                error = None if available else f"HTTP {response.status_code}"
                
                model_accessible = True  # DeepSeek model kontrolü
                
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
        DeepSeek maliyet tahmini (USD)
        deepseek-chat: ~$0.00014/1K input, $0.00028/1K output
        """
        input_cost = input_tokens / 1000 * 0.00014
        output_cost = output_tokens / 1000 * 0.00028
        return round(input_cost + output_cost, 6)