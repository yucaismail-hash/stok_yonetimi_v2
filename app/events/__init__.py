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
from app.events.publisher.event_publisher import EventPublisher
from app.events.repository.event_repository import EventRepository
from app.events.delivery.delivery_manager import DeliveryManager
from app.events.delivery.retry_policy import RetryPolicy
from app.events.subscribers.base_subscriber import BaseSubscriber
from app.events.subscribers.integration_subscriber import IntegrationSubscriber
from app.events.subscribers.internal_subscriber import InternalSubscriber
from app.events.subscribers.notification_subscriber import NotificationSubscriber
from app.events.lifecycle.lifecycle_manager import LifecycleManager
from app.events.versioning.event_version_manager import EventVersionManager

__all__ = [
    "EventBus",
    "EventFactory",
    "EventRegistry",
    "register_default_events",
    "Event",
    "EventStatus",
    "EventCategory",
    "EventPublisher",
    "EventRepository",
    "DeliveryManager",
    "RetryPolicy",
    "BaseSubscriber",
    "IntegrationSubscriber",
    "InternalSubscriber",
    "NotificationSubscriber",
    "LifecycleManager",
    "EventVersionManager",
]