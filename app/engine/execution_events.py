# app/engine/execution_events.py
"""
Execution Events - DOCUMENT 04A
Centralized execution lifecycle events.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4


class ExecutionEventType(str, Enum):
    """Centralized execution event types."""
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    
    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_SKIPPED = "task_skipped"
    TASK_RETRYING = "task_retrying"
    
    # Learning events
    LEARNING_STARTED = "learning_started"
    LEARNING_COMPLETED = "learning_completed"
    LEARNING_FAILED = "learning_failed"
    
    # Rule events
    RULE_EVALUATED = "rule_evaluated"
    RULE_APPLIED = "rule_applied"
    
    # Cache events
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    
    # Worker events
    WORKER_ASSIGNED = "worker_assigned"
    WORKER_COMPLETED = "worker_completed"
    WORKER_FAILED = "worker_failed"


@dataclass
class ExecutionEvent:
    """
    Execution Event - DOCUMENT 04A
    
    Immutable execution event.
    """
    event_id: str
    event_type: ExecutionEventType
    execution_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Optional fields
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    worker_id: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        event_type: ExecutionEventType,
        execution_id: str,
        task_id: Optional[str] = None,
        task_type: Optional[str] = None,
        worker_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> 'ExecutionEvent':
        """Create a new immutable execution event."""
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            execution_id=execution_id,
            task_id=task_id,
            task_type=task_type,
            worker_id=worker_id,
            error=error,
            metadata=metadata or {},
            timestamp=datetime.now(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "worker_id": self.worker_id,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class EventPublisher:
    """
    Event Publisher - Publishes execution events.
    """
    
    def __init__(self):
        self._subscribers = []
        self._event_history: list = []
        self._max_history = 1000
    
    def subscribe(self, callback):
        """Subscribe to events."""
        self._subscribers.append(callback)
    
    def publish(self, event: ExecutionEvent):
        """Publish an event to all subscribers."""
        # Store history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"Event subscriber error: {e}")
    
    def get_history(self, event_type: Optional[str] = None) -> list:
        """Get event history."""
        if event_type:
            return [e for e in self._event_history if e.event_type.value == event_type]
        return self._event_history
    
    def clear_history(self):
        """Clear event history."""
        self._event_history = []


# Global event publisher instance
event_publisher = EventPublisher()