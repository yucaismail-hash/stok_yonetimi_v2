# app/services/ai/provider_manager.py

import logging
from typing import Dict, Any, Optional, Type, List
from collections import defaultdict

from .base_provider import BaseAIProvider, AIResponse
from .ai_exceptions import (
    AIProviderError,
    FALLBACK_ERRORS,
    NO_FALLBACK_ERRORS,
    AIProviderConnectionError,
)
from .config import AIConfig
from .gemini_provider import GeminiProvider
# İleride eklenecek:
from .deepseek_provider import DeepSeekProvider
from .openai_provider import OpenAIProvider
# from .claude_provider import ClaudeProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Provider Manager - Sistemin beyni
    
    Görevleri:
    - Aktif provider'ı seçmek
    - Fallback yapmak
    - Retry yapmak
    - Provider değiştirmek
    - Sağlık kontrolü yapmak
    - Kullanım istatistiklerini üretmek
    """
    
    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._provider_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "total_time_ms": 0,
            "last_error": None,
            "last_success": None,
        })
        self._active_provider: Optional[str] = None
        self._provider_order = AIConfig.PROVIDER_ORDER
        
        # Provider'ları kaydet
        self._register_provider("gemini", GeminiProvider)
        self._register_provider("deepseek", DeepSeekProvider)
        self._register_provider("openai", OpenAIProvider)
        # self._register_provider("claude", ClaudeProvider)
        
        # İlk active provider'ı seç
        self._set_active_provider(AIConfig.PROVIDER)
    
    def _register_provider(self, name: str, provider_class: Type[BaseAIProvider], **kwargs):
        """Yeni bir provider kaydeder"""
        try:
            provider = provider_class(**kwargs)
            self._providers[name] = provider
            logger.info(f"✅ Provider kaydedildi: {name} ({provider.model_name})")
        except Exception as e:
            logger.warning(f"⚠️ Provider kaydedilemedi: {name} - {e}")
    
    def _set_active_provider(self, name: str):
        """Aktif provider'ı değiştir"""
        if name in self._providers:
            self._active_provider = name
            logger.info(f"🔄 Aktif provider: {name}")
        else:
            logger.warning(f"⚠️ Provider bulunamadı: {name}, varsayılana geçiliyor")
            self._active_provider = self._provider_order[0] if self._provider_order else "gemini"
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """
        Prompt gönderir. Gerekirse fallback yapar.
        
        Args:
            prompt: Gönderilecek prompt
            **kwargs: temperature, max_tokens, etc.
        
        Returns:
            AIResponse: Provider'dan gelen yanıt
        
        Raises:
            AIProviderError: Tüm provider'lar başarısız olursa
        """
        last_error = None
        
        # Hangi provider'ları dene
        providers_to_try = self._get_providers_to_try()
        
        for provider_name in providers_to_try:
            try:
                provider = self._providers.get(provider_name)
                if not provider:
                    continue
                
                logger.info(f"🔮 AI çağrısı yapılıyor: {provider_name} ({provider.model_name})")
                
                response = provider.generate(prompt, **kwargs)
                
                # İstatistikleri güncelle
                self._update_stats(provider_name, success=True, response_time=response.response_time_ms)
                
                # Başarılı provider'ı aktif yap
                if provider_name != self._active_provider:
                    self._set_active_provider(provider_name)
                
                return response
                
            except Exception as e:
                last_error = e
                self._update_stats(provider_name, success=False, error=str(e))
                
                # Fallback yapılabilir mi kontrol et
                should_fallback = self._should_fallback(e)
                
                if should_fallback and AIConfig.FALLBACK:
                    logger.warning(f"⚠️ {provider_name} başarısız, fallback deneniyor: {e}")
                    continue
                elif not should_fallback:
                    # Fallback yapılamayacak hata - doğrudan fırlat
                    raise
        
        # Tüm provider'lar başarısız
        raise AIProviderError(
            f"Tüm AI provider'ları başarısız. Son hata: {last_error}",
            provider=None,
            original_error=last_error
        )
    
    def _get_providers_to_try(self) -> List[str]:
        """Hangi provider'ların denenmesi gerektiğini döndürür"""
        # Önce aktif provider
        providers = []
        
        if self._active_provider and self._active_provider in self._providers:
            providers.append(self._active_provider)
        
        # Sonra sıradaki provider'lar (aktif provider hariç)
        for p in self._provider_order:
            if p != self._active_provider and p in self._providers:
                providers.append(p)
        
        # Eğer aktif provider listede yoksa, ilk provider'ı ekle
        if not providers:
            for p in self._provider_order:
                if p in self._providers:
                    providers.append(p)
                    break
        
        return providers
    
    def _should_fallback(self, error: Exception) -> bool:
        """Bu hata için fallback yapılabilir mi?"""
        for fallback_error in FALLBACK_ERRORS:
            if isinstance(error, fallback_error):
                return True
        return False
    
    def _update_stats(self, provider_name: str, success: bool, response_time: float = None, error: str = None):
        """Provider istatistiklerini günceller"""
        stats = self._provider_stats[provider_name]
        stats["total_calls"] += 1
        
        if success:
            stats["success_calls"] += 1
            if response_time:
                stats["total_time_ms"] += response_time
            stats["last_success"] = None  # timestamp eklenebilir
        else:
            stats["failed_calls"] += 1
            stats["last_error"] = error
    
    def get_stats(self) -> Dict[str, Any]:
        """Tüm provider istatistiklerini döndürür"""
        result = {}
        for name, stats in self._provider_stats.items():
            total = stats["total_calls"]
            success_rate = (stats["success_calls"] / total * 100) if total > 0 else 0
            avg_time = (stats["total_time_ms"] / stats["success_calls"]) if stats["success_calls"] > 0 else 0
            
            result[name] = {
                "total_calls": total,
                "success_calls": stats["success_calls"],
                "failed_calls": stats["failed_calls"],
                "success_rate": round(success_rate, 2),
                "avg_response_time_ms": round(avg_time, 2),
                "last_error": stats["last_error"],
                "is_active": name == self._active_provider,
                "available": name in self._providers,
            }
        return result
    
    def health_check_all(self) -> Dict[str, Any]:
        """Tüm provider'ların sağlık durumunu kontrol eder"""
        result = {}
        for name, provider in self._providers.items():
            result[name] = provider.health_check()
        return result
    
    def get_provider(self, name: str) -> Optional[BaseAIProvider]:
        """Provider'ı döndürür"""
        return self._providers.get(name)
    
    def get_active_provider(self) -> Optional[BaseAIProvider]:
        """Aktif provider'ı döndürür"""
        if self._active_provider:
            return self._providers.get(self._active_provider)
        return None


# Singleton instance
_provider_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """Singleton Provider Manager döndürür"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager