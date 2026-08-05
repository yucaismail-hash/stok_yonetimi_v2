# app/rate_limiter/rate_limiter.py
"""
Rate Limiter - DOCUMENT 07 APP-044 / REVISION 07

Rate Limiter SHALL become provider independent.
Future implementations SHALL support:
- Memory
- Redis
- Distributed Cache

without architectural changes.
"""

from typing import Optional, Dict, Any
import time
import logging

from app.rate_limiter.providers.memory_provider import MemoryProvider

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate Limiter - Provider independent rate limiting.
    
    Supports:
    - Per User limits
    - Per Company limits
    - Per API Key limits
    - Per Integration limits
    """
    
    def __init__(self, provider=None):
        self.provider = provider or MemoryProvider()
        self.configs: Dict[str, Dict[str, Any]] = {}
    
    def configure(self, key: str, limit: int, window: int) -> None:
        """
        Configure rate limit for a key.
        
        Args:
            key: Identifier (user_id, company_id, api_key, etc.)
            limit: Maximum requests
            window: Time window in seconds
        """
        self.configs[key] = {
            "limit": limit,
            "window": window,
        }
        logger.info(f"Rate limit configured: {key} -> {limit} per {window}s")
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed.
        
        Returns:
            bool: True if allowed, False if rate limited
        """
        config = self.configs.get(key)
        if not config:
            # No limit configured, allow by default
            return True
        
        limit = config["limit"]
        window = config["window"]
        
        current = int(time.time())
        count = self.provider.get_count(key, current, window)
        
        if count >= limit:
            logger.warning(f"Rate limit exceeded: {key} ({count}/{limit})")
            return False
        
        self.provider.increment(key, current, window)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        config = self.configs.get(key)
        if not config:
            return 0
        
        limit = config["limit"]
        current = int(time.time())
        window = config["window"]
        count = self.provider.get_count(key, current, window)
        
        return max(0, limit - count)
    
    def get_reset_time(self, key: str) -> int:
        """Get reset time for key."""
        config = self.configs.get(key)
        if not config:
            return 0
        
        current = int(time.time())
        window = config["window"]
        
        # Reset at the end of the window
        return current + window