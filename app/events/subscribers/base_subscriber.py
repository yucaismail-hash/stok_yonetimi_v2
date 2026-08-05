# app/events/subscribers/base_subscriber.py
"""
Base Subscriber - DOCUMENT 07 REVISION 04

Subscribers SHALL represent communication type
instead of vendor implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from app.events.models.event import Event

logger = logging.getLogger(__name__)


class BaseSubscriber(ABC):
    """
    Base Subscriber - All subscribers SHALL inherit from this.
    
    Subscribers SHALL NOT communicate directly with analytical engines.
    """
    
    def __init__(self, name: str):
        self.name = name
        self._event_types: List[str] = []
    
    def subscribe_to(self, event_type: str) -> None:
        """Subscribe to an event type."""
        if event_type not in self._event_types:
            self._event_types.append(event_type)
            logger.info(f"{self.name} subscribed to: {event_type}")
    
    def subscribe_to_many(self, event_types: List[str]) -> None:
        """Subscribe to multiple event types."""
        for event_type in event_types:
            self.subscribe_to(event_type)
    
    def can_handle(self, event: Event) -> bool:
        """Check if this subscriber can handle the event."""
        return event.event_type in self._event_types
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """
        Handle an Event.
        
        Subscribers SHALL NOT:
        - Execute workflows
        - Execute business logic
        - Trigger analytical calculations
        - Perform persistence directly
        
        Subscribers SHALL only consume Events.
        """
        pass
    
    @abstractmethod
    def get_subscriber_type(self) -> str:
        """Get subscriber type."""
        pass