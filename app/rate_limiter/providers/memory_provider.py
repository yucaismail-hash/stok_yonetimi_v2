# app/rate_limiter/providers/memory_provider.py
"""
Memory Provider - DOCUMENT 07 REVISION 07

In-memory rate limit storage.
"""

from typing import Dict, List
import time


class MemoryProvider:
    """
    Memory Provider - In-memory rate limit storage.
    
    Suitable for development and single-instance deployments.
    """
    
    def __init__(self):
        self._storage: Dict[str, List[int]] = {}
    
    def get_count(self, key: str, current_time: int, window: int) -> int:
        """
        Get request count for key within window.
        """
        if key not in self._storage:
            return 0
        
        # Clean old entries
        cutoff = current_time - window
        self._storage[key] = [
            t for t in self._storage[key] if t > cutoff
        ]
        
        return len(self._storage[key])
    
    def increment(self, key: str, current_time: int, window: int) -> None:
        """
        Increment request count for key.
        """
        if key not in self._storage:
            self._storage[key] = []
        
        # Clean old entries
        cutoff = current_time - window
        self._storage[key] = [
            t for t in self._storage[key] if t > cutoff
        ]
        
        # Add current request
        self._storage[key].append(current_time)
    
    def reset(self, key: str) -> None:
        """
        Reset rate limit for key.
        """
        if key in self._storage:
            del self._storage[key]