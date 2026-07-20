# app/services/ai/ai_health.py

import logging
from typing import Dict, Any
from datetime import datetime

from .provider_manager import get_provider_manager

logger = logging.getLogger(__name__)


class AIHealthChecker:
    """AI Provider sağlık kontrolü"""
    
    def __init__(self):
        self.manager = get_provider_manager()
        self._last_check: Dict[str, Any] = {}
        self._health_cache: Dict[str, Any] = {}
    
    def check_all(self, force: bool = False) -> Dict[str, Any]:
        """
        Tüm provider'ları kontrol eder.
        
        Args:
            force: Zorla yeniden kontrol et
        
        Returns:
            {
                "timestamp": "2024-01-01T00:00:00",
                "providers": {
                    "gemini": {
                        "available": True,
                        "model_accessible": True,
                        "response_time_ms": 123,
                        "error": None
                    }
                }
            }
        """
        if not force and self._health_cache:
            return self._health_cache
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "providers": self.manager.health_check_all(),
        }
        
        self._health_cache = result
        return result
    
    def get_available_providers(self) -> list:
        """Kullanılabilir provider'ları döndürür"""
        health = self.check_all()
        available = []
        for name, status in health.get("providers", {}).items():
            if status.get("available") and status.get("model_accessible"):
                available.append(name)
        return available
    
    def is_provider_healthy(self, provider_name: str) -> bool:
        """Belirli bir provider sağlıklı mı?"""
        health = self.check_all()
        status = health.get("providers", {}).get(provider_name, {})
        return status.get("available", False) and status.get("model_accessible", False)