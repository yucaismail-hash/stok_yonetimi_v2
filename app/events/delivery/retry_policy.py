# app/events/delivery/retry_policy.py
"""
Retry Policy - DOCUMENT 07 APP-039

Defines retry behavior for Event delivery.
"""

from typing import Optional
import random


class RetryPolicy:
    """
    Retry Policy - Defines retry behavior.
    
    Supports:
    - Exponential backoff
    - Max retry limit
    - Jitter for distributed systems
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: int = 5,
        max_delay: int = 300,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def should_retry(self, attempt: int) -> bool:
        """Check if retry should be attempted."""
        return attempt < self.max_retries
    
    def get_delay(self, attempt: int) -> int:
        """
        Get delay for retry attempt.
        
        Uses exponential backoff with jitter.
        """
        # Exponential backoff: base_delay * 2^attempt
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Add jitter for distributed systems
        jitter = random.uniform(0, 1) * 0.5 * delay
        delay = delay + jitter
        
        return int(delay)
    
    def get_max_retries(self) -> int:
        """Get maximum retry count."""
        return self.max_retries
    
    def get_remaining_retries(self, attempt: int) -> int:
        """Get remaining retry attempts."""
        return max(0, self.max_retries - attempt)