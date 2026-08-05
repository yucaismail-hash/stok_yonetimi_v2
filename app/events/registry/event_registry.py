# app/events/registry/event_registry.py
"""
Event Registry - DOCUMENT 07 REVISION 03

The platform SHALL register every supported Event centrally.
Future Events SHALL be registered without changing platform architecture.
"""

from typing import Dict, Any, Optional, List, datetime
import logging

logger = logging.getLogger(__name__)


class EventRegistry:
    """
    Event Registry - Central registry for all supported Events.
    
    Every supported Event SHALL be registered here.
    Future Events SHALL be registered without changing platform architecture.
    """
    
    _instance = None
    _events: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(
        self,
        event_type: str,
        version: str = "1.0",
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Register an event type.
        
        Args:
            event_type: Unique event type identifier
            version: Event version
            category: Event category (dataset, execution, artifact, learning, integration)
            description: Event description
        """
        self._events[event_type] = {
            "event_type": event_type,
            "version": version,
            "category": category,
            "description": description,
            "registered_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"Registered event: {event_type}")
    
    def get_event(self, event_type: str) -> Optional[Dict[str, Any]]:
        """Get event registration details."""
        return self._events.get(event_type)
    
    def is_registered(self, event_type: str) -> bool:
        """Check if event type is registered."""
        return event_type in self._events
    
    def list_events(self) -> List[Dict[str, Any]]:
        """List all registered events."""
        return list(self._events.values())
    
    def list_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List events by category."""
        return [
            event for event in self._events.values()
            if event.get("category") == category
        ]
    
    def get_version(self, event_type: str) -> Optional[str]:
        """Get event version."""
        event = self.get_event(event_type)
        return event.get("version") if event else None
    
    def clear(self) -> None:
        """Clear all registered events."""
        self._events.clear()
        logger.info("Cleared all event registrations")


# Initialize registry with standard events
def register_default_events():
    """Register default event types."""
    registry = EventRegistry()
    
    # Dataset Events
    registry.register("dataset.uploaded", category="dataset", description="Dataset uploaded")
    registry.register("dataset.validated", category="dataset", description="Dataset validated")
    registry.register("dataset.approved", category="dataset", description="Dataset approved")
    registry.register("dataset.failed", category="dataset", description="Dataset validation failed")
    
    # Execution Events
    registry.register("execution.started", category="execution", description="Execution started")
    registry.register("execution.completed", category="execution", description="Execution completed")
    registry.register("execution.failed", category="execution", description="Execution failed")
    registry.register("execution.learning", category="execution", description="Learning started")
    registry.register("execution.deciding", category="execution", description="Decision Intelligence started")
    
    # Artifact Events
    registry.register("artifact.created", category="artifact", description="AI Artifact created")
    registry.register("artifact.published", category="artifact", description="AI Artifact published")
    registry.register("artifact.reused", category="artifact", description="AI Artifact reused")
    registry.register("artifact.archived", category="artifact", description="AI Artifact archived")
    
    # Learning Events
    registry.register("learning.updated", category="learning", description="Learning updated")
    registry.register("learning.pattern_detected", category="learning", description="Pattern detected")
    registry.register("learning.confidence_updated", category="learning", description="Confidence updated")
    
    # Integration Events
    registry.register("integration.sync_started", category="integration", description="Integration sync started")
    registry.register("integration.sync_completed", category="integration", description="Integration sync completed")
    registry.register("integration.sync_failed", category="integration", description="Integration sync failed")