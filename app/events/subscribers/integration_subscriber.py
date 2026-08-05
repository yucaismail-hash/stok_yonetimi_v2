# app/events/subscribers/integration_subscriber.py
"""
Integration Subscriber - DOCUMENT 07 REVISION 04

Handles Events for external integrations.
ERP specific behavior SHALL remain inside Integration Adapters.
"""

from typing import Dict, Any
import logging

from app.events.subscribers.base_subscriber import BaseSubscriber
from app.events.models.event import Event
from app.integration.adapters.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class IntegrationSubscriber(BaseSubscriber):
    """
    Integration Subscriber - Handles Events for external integrations.
    
    Subscribers SHALL represent communication type
    instead of vendor implementations.
    """
    
    def __init__(self, name: str = "integration_subscriber", adapter: BaseAdapter = None):
        super().__init__(name)
        self.adapter = adapter
        
        # Subscribe to relevant events
        self.subscribe_to_many([
            "execution.completed",
            "artifact.created",
            "artifact.published",
            "integration.sync_completed",
        ])
    
    async def handle(self, event: Event) -> None:
        """
        Handle an Event for external integration.
        """
        logger.info(f"📬 IntegrationSubscriber handling: {event.event_type}")
        
        if not self.adapter:
            logger.warning("No adapter configured for IntegrationSubscriber")
            return
        
        try:
            # Map event to external format
            external_payload = self._map_event_to_external(event)
            
            # Send to external system via adapter
            await self.adapter.process(external_payload)
            
        except Exception as e:
            logger.error(f"IntegrationSubscriber error: {e}")
    
    def _map_event_to_external(self, event: Event) -> Dict[str, Any]:
        """Map internal event to external payload."""
        return {
            "event_type": event.event_type,
            "event_id": str(event.event_id),
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "data": event.payload,
            "metadata": event.metadata,
        }
    
    def get_subscriber_type(self) -> str:
        return "integration"