# app/events/registry/__init__.py
"""Event Registry - DOCUMENT 07 REVISION 03."""
from app.events.registry.event_registry import EventRegistry, register_default_events

__all__ = [
    "EventRegistry",
    "register_default_events",
]