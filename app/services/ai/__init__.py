# app/services/ai/__init__.py
"""
AI Services - DOCUMENT 01 AI Architecture
"""

from .base_provider import BaseAIProvider, AIResponse
from .provider_manager import ProviderManager, get_provider_manager
from .ai_decision_engine import AIDecisionEngine
from .prompt_builder import PromptBuilder
from .config import AIConfig

# Provider'lar
from .gemini_provider import GeminiProvider
from .deepseek_provider import DeepSeekProvider
from .openai_provider import OpenAIProvider

# Exception'lar
from .ai_exceptions import (
    AIProviderError,
    AIProviderTimeoutError,
    AIProviderConnectionError,
    AIProviderRateLimitError,
    AIProviderModelNotFoundError,
    AIProviderServerError,
    AIAuthenticationError,
)

__all__ = [
    # Core
    "BaseAIProvider",
    "AIResponse",
    "ProviderManager",
    "get_provider_manager",
    "AIDecisionEngine",
    "PromptBuilder",
    "AIConfig",
    # Providers
    "GeminiProvider",
    "DeepSeekProvider",
    "OpenAIProvider",
    # Exceptions
    "AIProviderError",
    "AIProviderTimeoutError",
    "AIProviderConnectionError",
    "AIProviderRateLimitError",
    "AIProviderModelNotFoundError",
    "AIProviderServerError",
    "AIAuthenticationError",
]