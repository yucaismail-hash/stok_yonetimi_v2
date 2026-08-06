# app/events/__init__.py
"""
Events - DOCUMENT 07 PART 05

Events SHALL represent Business Facts.
Commands request work. Executions perform work.
AI Artifacts describe results. Events announce completed facts.
"""

from app.events.event_bus import EventBus
from app.events.factory.event_factory import EventFactory
from app.events.registry.event_registry import EventRegistry, register_default_events
from app.events.models.event import Event, EventStatus, EventCategory
from app.events.repository.event_repository import EventRepository
from app.events.delivery.delivery_manager import DeliveryManager
from app.events.delivery.retry_policy import RetryPolicy
from app.events.subscribers.base_subscriber import BaseSubscriber
from app.events.subscribers.integration_subscriber import IntegrationSubscriber
from app.events.subscribers.notification_subscriber import NotificationSubscriber

__all__ = [
    "EventBus",
    "EventFactory",
    "EventRegistry",
    "register_default_events",
    "Event",
    "EventStatus",
    "EventCategory",
    "EventRepository",
    "DeliveryManager",
    "RetryPolicy",
    "BaseSubscriber",
    "IntegrationSubscriber",
    "NotificationSubscriber",
]
