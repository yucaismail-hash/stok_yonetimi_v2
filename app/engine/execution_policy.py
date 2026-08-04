# app/engine/execution_policy.py
"""
Execution Policy - DOCUMENT 04A
Centralized execution policies.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class RetryPolicy(str, Enum):
    """Retry policy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    NO_RETRY = "no_retry"


class TimeoutPolicy(str, Enum):
    """Timeout policy types."""
    HARD_TIMEOUT = "hard_timeout"
    SOFT_TIMEOUT = "soft_timeout"
    NO_TIMEOUT = "no_timeout"


@dataclass
class RetryConfig:
    """Retry configuration."""
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a retry attempt."""
        if self.policy == RetryPolicy.NO_RETRY:
            return 0.0
        
        if self.policy == RetryPolicy.FIXED_DELAY:
            return self.initial_delay_seconds
        
        # Exponential backoff
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_seconds)


@dataclass
class TimeoutConfig:
    """Timeout configuration."""
    policy: TimeoutPolicy = TimeoutPolicy.HARD_TIMEOUT
    default_seconds: int = 300  # 5 minutes
    max_seconds: int = 3600  # 1 hour


@dataclass
class ParallelExecutionConfig:
    """Parallel execution configuration."""
    max_parallel_tasks: int = 4
    max_parallel_per_worker: int = 2
    enable_parallel: bool = True


@dataclass
class ExecutionPolicy:
    """
    Execution Policy - DOCUMENT 04A
    
    Centralized execution behavior configuration.
    """
    
    # Retry policy
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    
    # Timeout policy
    timeout_config: TimeoutConfig = field(default_factory=TimeoutConfig)
    
    # Parallel execution policy
    parallel_config: ParallelExecutionConfig = field(default_factory=ParallelExecutionConfig)
    
    # Resource limits
    max_cpu_percent: float = 80.0
    max_memory_mb: int = 4096
    
    # Task-specific overrides
    task_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def get_retry_config(self, task_type: Optional[str] = None) -> RetryConfig:
        """Get retry configuration for a task."""
        if task_type and task_type in self.task_overrides:
            override = self.task_overrides[task_type]
            if "retry" in override:
                return RetryConfig(**override["retry"])
        
        return self.retry_config
    
    def get_timeout_config(self, task_type: Optional[str] = None) -> TimeoutConfig:
        """Get timeout configuration for a task."""
        if task_type and task_type in self.task_overrides:
            override = self.task_overrides[task_type]
            if "timeout" in override:
                return TimeoutConfig(**override["timeout"])
        
        return self.timeout_config
    
    def get_parallel_config(self) -> ParallelExecutionConfig:
        """Get parallel execution configuration."""
        return self.parallel_config
    
    def get_task_retry_count(self, task_type: str) -> int:
        """Get retry count for a task type."""
        config = self.get_retry_config(task_type)
        return config.max_retries
    
    def get_task_timeout(self, task_type: str) -> int:
        """Get timeout for a task type."""
        config = self.get_timeout_config(task_type)
        return config.default_seconds


# Default execution policy
default_execution_policy = ExecutionPolicy()


# Task-specific overrides for known task types
default_execution_policy.task_overrides = {
    "forecast": {
        "retry": {"max_retries": 3, "initial_delay_seconds": 2.0},
        "timeout": {"default_seconds": 600},
    },
    "simulation": {
        "retry": {"max_retries": 2, "initial_delay_seconds": 5.0},
        "timeout": {"default_seconds": 900},
    },
    "backtest": {
        "retry": {"max_retries": 2, "initial_delay_seconds": 2.0},
        "timeout": {"default_seconds": 300},
    },
    "safety_stock": {
        "retry": {"max_retries": 3, "initial_delay_seconds": 1.0},
        "timeout": {"default_seconds": 300},
    },
    "supplier": {
        "retry": {"max_retries": 2, "initial_delay_seconds": 2.0},
        "timeout": {"default_seconds": 300},
    },
}