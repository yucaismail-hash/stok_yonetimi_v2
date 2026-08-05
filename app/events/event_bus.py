# app/events/event_bus.py
"""
Event Bus - DOCUMENT 07 REVISION 01

The Event Bus SHALL become the only internal communication channel for Events.
Every platform component SHALL publish Events only through Event Bus.

Event Publisher SHALL publish only to Event Bus.
Future delivery mechanisms SHALL subscribe to Event Bus.

Official Flow:
Execution Engine → Event Factory → Event Bus → Repository → Delivery Manager
"""

from typing import List, Callable, Optional, Dict, Any, UUID
import asyncio
import logging

from app.events.models.event import Event, EventStatus
from app.events.repository.event_repository import EventRepository
from app.events.delivery.delivery_manager import DeliveryManager

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event Bus - Internal communication channel for Events.
    
    Every platform component SHALL publish Events only through Event Bus.
    """
    
    _instance = None
    _subscribers: List[Callable] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.repository = EventRepository()
        self.delivery_manager = DeliveryManager()
    
    async def publish(self, event: Event) -> None:
        """
        Publish an Event to the Event Bus.
        
        Steps:
        1. Persist Event (Repository)
        2. Notify internal subscribers
        3. Queue for delivery
        """
        logger.info(f"📤 Publishing event: {event.event_type} (ID: {event.event_id})")
        
        try:
            # 1. Persist Event
            persisted = await self.repository.save(event)
            
            # 2. Update status
            persisted = persisted.with_status(EventStatus.PUBLISHED)
            await self.repository.update(persisted)
            
            # 3. Notify internal subscribers (synchronous)
            for subscriber in self._subscribers:
                try:
                    await subscriber(persisted)
                except Exception as e:
                    logger.error(f"Subscriber error: {e}")
            
            # 4. Queue for external delivery
            await self.delivery_manager.enqueue(persisted)
            
            logger.info(f"✅ Event published: {event.event_type} (ID: {event.event_id})")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            # Update status to failed
            failed_event = event.with_status(EventStatus.FAILED)
            await self.repository.update(failed_event)
            raise
    
    def subscribe(self, subscriber: Callable) -> None:
        """Register an internal subscriber."""
        self._subscribers.append(subscriber)
        logger.info(f"Subscriber registered: {subscriber.__name__}")
    
    def unsubscribe(self, subscriber: Callable) -> None:
        """Unregister an internal subscriber."""
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
            logger.info(f"Subscriber unregistered: {subscriber.__name__}")
    
    async def get_event(self, event_id: UUID) -> Optional[Event]:
        """Get an Event by ID."""
        return await self.repository.get_by_id(event_id)
    
    async def get_events_by_execution(self, execution_id: UUID) -> List[Event]:
        """Get Events by execution ID."""
        return await self.repository.get_by_execution(execution_id)
    
    async def get_events_by_company(self, company_id: UUID) -> List[Event]:
        """Get Events by company ID."""
        return await self.repository.get_by_company(company_id)