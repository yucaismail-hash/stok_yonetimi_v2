# app/services/ai/base_provider.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AIResponse:
    """AI Provider'dan gelen standart yanıt"""
    content: str
    provider: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    response_time_ms: Optional[float] = None


class BaseAIProvider(ABC):
    """
    Tüm AI sağlayıcıları için temel sınıf.
    Her provider bu interface'i implemente etmelidir.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider adı (örn: 'gemini', 'openai')"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Kullanılan model adı"""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """
        Prompt gönderir ve AIResponse döndürür.
        
        Args:
            prompt: Gönderilecek prompt
            **kwargs: temperature, max_tokens, etc.
        
        Returns:
            AIResponse: Standart yanıt nesnesi
        
        Raises:
            AIProviderTimeoutError: Zaman aşımı
            AIProviderConnectionError: Bağlantı hatası
            AIProviderRateLimitError: Kot aşımı
            AIProviderModelNotFoundError: Model bulunamadı
            AIAuthenticationError: API key geçersiz
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Provider'ın sağlık durumunu kontrol eder.
        
        Returns:
            {
                "available": True/False,
                "model_accessible": True/False,
                "response_time_ms": 123,
                "error": None or "error message"
            }
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Metnin token sayısını tahmin eder"""
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Token maliyetini tahmin eder (USD cinsinden)"""
        pass
    
    def can_handle_error(self, error: Exception) -> bool:
        """
        Bu provider bu hatayı handle edebilir mi?
        Varsayılan: True (tüm hataları dener)
        """
        return True