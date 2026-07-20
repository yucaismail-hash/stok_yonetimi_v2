# app/services/ai/config.py - GÜNCELLENMİŞ

import os
from typing import Optional
from dotenv import load_dotenv  # ✅ EKLE

# ✅ .env dosyasını yükle
load_dotenv()


class AIConfig:
    """AI Konfigürasyonu - .env'den okur"""
    
    # Provider
    PROVIDER = os.getenv("AI_PROVIDER", "gemini")
    MODEL = os.getenv("AI_MODEL", "gemini-3.1-flash-lite")
    
    # Timeout & Retry
    TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))
    RETRY = int(os.getenv("AI_RETRY", "3"))
    FALLBACK = os.getenv("AI_FALLBACK", "true").lower() == "true"
    
    # Token & Temperature
    MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "1200"))
    TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    
    # Provider sırası (fallback için)
    PROVIDER_ORDER = os.getenv("AI_PROVIDER_ORDER", "gemini,deepseek,openai,claude").split(",")
    
    @classmethod
    def get_provider_config(cls, provider: str) -> dict:
        """Provider'a özel konfigürasyon döndürür"""
        configs = {
            "gemini": {
                "api_key": cls.GEMINI_API_KEY,
                "model": cls.MODEL,
                "timeout": cls.TIMEOUT,
            },
            "deepseek": {
                "api_key": cls.DEEPSEEK_API_KEY,
                "model": "deepseek-chat",
                "timeout": cls.TIMEOUT,
            },
            "openai": {
                "api_key": cls.OPENAI_API_KEY,
                "model": "gpt-4o-mini",
                "timeout": cls.TIMEOUT,
            },
            "claude": {
                "api_key": cls.CLAUDE_API_KEY,
                "model": "claude-3-haiku-20240307",
                "timeout": cls.TIMEOUT,
            },
        }
        return configs.get(provider, {})
    
    @classmethod
    def print_status(cls):
        """Mevcut konfigürasyon durumunu yazdırır"""
        print("=" * 50)
        print("📋 AI Konfigürasyon Durumu")
        print("=" * 50)
        print(f"  AI_PROVIDER: {cls.PROVIDER}")
        print(f"  AI_MODEL: {cls.MODEL}")
        print(f"  AI_TIMEOUT: {cls.TIMEOUT}")
        print(f"  AI_RETRY: {cls.RETRY}")
        print(f"  AI_FALLBACK: {cls.FALLBACK}")
        print(f"  AI_MAX_TOKENS: {cls.MAX_TOKENS}")
        print(f"  AI_TEMPERATURE: {cls.TEMPERATURE}")
        print(f"  PROVIDER_ORDER: {cls.PROVIDER_ORDER}")
        print("-" * 50)
        print(f"  GEMINI_API_KEY: {'✅ Var' if cls.GEMINI_API_KEY else '❌ Yok'}")
        print(f"  DEEPSEEK_API_KEY: {'✅ Var' if cls.DEEPSEEK_API_KEY else '❌ Yok'}")
        print(f"  OPENAI_API_KEY: {'✅ Var' if cls.OPENAI_API_KEY else '❌ Yok'}")
        print(f"  CLAUDE_API_KEY: {'✅ Var' if cls.CLAUDE_API_KEY else '❌ Yok'}")
        print("=" * 50)