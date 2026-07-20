# app/services/ai/ai_exceptions.py

"""
AI Katmanı Özel Exception'ları
"""


class AIProviderError(Exception):
    """AI Provider ile ilgili tüm hataların base sınıfı"""
    def __init__(self, message: str, provider: str = None, original_error: Exception = None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(message)


class AIProviderTimeoutError(AIProviderError):
    """Zaman aşımı hatası (Fallback tetikler)"""
    pass


class AIProviderConnectionError(AIProviderError):
    """Bağlantı hatası (DNS, Network) - Fallback tetikler"""
    pass


class AIProviderRateLimitError(AIProviderError):
    """Kot aşımı (429) - Fallback tetikler"""
    pass


class AIProviderModelNotFoundError(AIProviderError):
    """Model bulunamadı (404) - Fallback tetikler"""
    pass


class AIProviderServerError(AIProviderError):
    """Sunucu hatası (500, 502, 503, 504) - Fallback tetikler"""
    pass


class AIAuthenticationError(AIProviderError):
    """Kimlik doğrulama hatası (API Key geçersiz) - Fallback tetiklemez"""
    pass


class AIPromptError(AIProviderError):
    """Prompt ile ilgili hata - Fallback tetiklemez"""
    pass


class AIJSONParseError(AIProviderError):
    """JSON parse hatası - Fallback tetiklemez"""
    pass


class AIValidationError(AIProviderError):
    """Validasyon hatası - Fallback tetiklemez"""
    pass


# Hata sınıflandırması
FALLBACK_ERRORS = (
    AIProviderTimeoutError,
    AIProviderConnectionError,
    AIProviderRateLimitError,
    AIProviderModelNotFoundError,
    AIProviderServerError,
)

NO_FALLBACK_ERRORS = (
    AIAuthenticationError,
    AIPromptError,
    AIJSONParseError,
    AIValidationError,
)