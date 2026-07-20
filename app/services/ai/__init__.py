# app/services/ai/__init__.py - GÜNCELLENMİŞ

from .llm_service import LLMService, get_llm_service
from .provider_manager import ProviderManager, get_provider_manager
from .prompt_builder import PromptBuilder
from .ai_exceptions import *
from .ai_health import AIHealthChecker
from .config import AIConfig
from .gemini_provider import GeminiProvider
from .deepseek_provider import DeepSeekProvider  # ✅ YENİ
from .openai_provider import OpenAIProvider  # ✅ BUNU EKLE

__all__ = [
    "LLMService",
    "get_llm_service",
    "ProviderManager",
    "get_provider_manager",
    "PromptBuilder",
    "AIHealthChecker",
    "AIConfig",
    "GeminiProvider",
    "DeepSeekProvider",  # ✅ YENİ
    "OpenAIProvider",  # ✅ BUNU EKLE
    # Exception'lar
    "AIProviderError",
    "AIProviderTimeoutError",
    "AIProviderConnectionError",
    "AIProviderRateLimitError",
    "AIProviderModelNotFoundError",
    "AIProviderServerError",
    "AIAuthenticationError",
    "AIPromptError",
    "AIJSONParseError",
    "AIValidationError",
]