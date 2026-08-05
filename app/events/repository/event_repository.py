# app/events/repository/event_repository.py
"""
Event Repository - DOCUMENT 07 APP-034 / REVISION 07

Event Repository SHALL become the official Event Audit Log.

Every stored Event SHALL contain:
- Event
- Payload
- Metadata
- Publisher
- Source Component
- Creation Time
- Correlation ID
- Trace ID
- Delivery Status
- Retry History
- Acknowledgement Status
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from app.events.models.event import Event, EventStatus

logger = logging.getLogger(__name__)


class EventRepository:
    """
    Event Repository - Official Event Audit Log.
    
    Every published Event SHALL be persisted.
    Supports audit, debugging, retry, and historical analysis.
    """
    
    # In-memory storage (replace with PostgreSQL in production)
    _storage: Dict[UUID, Event] = {}
    _delivery_status: Dict[UUID, Dict[str, Any]] = {}
    
    async def save(self, event: Event) -> Event:
        """Save an Event to the repository."""
        self._storage[event.event_id] = event
        self._delivery_status[event.event_id] = {
            "status": event.status.value if event.status else "created",
            "retry_count": 0,
            "attempts": [],
            "acknowledged": False,
            "acknowledged_at": None,
        }
        logger.info(f"Event saved: {event.event_id}")
        return event
    
    async def update(self, event: Event) -> Event:
        """Update an Event in the repository."""
        self._storage[event.event_id] = event
        logger.info(f"Event updated: {event.event_id}")
        return event
    
    async def get_by_id(self, event_id: UUID) -> Optional[Event]:
        """Get an Event by ID."""
        return self._storage.get(event_id)
    
    async def get_by_execution(self, execution_id: UUID) -> List[Event]:
        """Get Events by execution ID."""
        return [
            event for event in self._storage.values()
            if event.execution_id == execution_id
        ]
    
    async def get_by_company(self, company_id: UUID) -> List[Event]:
        """Get Events by company ID."""
        return [
            event for event in self._storage.values()
            if event.company_id == company_id
        ]
    
    async def get_by_type(self, event_type: str) -> List[Event]:
        """Get Events by type."""
        return [
            event for event in self._storage.values()
            if event.event_type == event_type
        ]
    
    async def get_delivery_status(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """Get delivery status for an Event."""
        return self._delivery_status.get(event_id)
    
    async def update_delivery_status(
        self,
        event_id: UUID,
        status: str,
        attempt: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update delivery status."""
        if event_id in self._delivery_status:
            self._delivery_status[event_id]["status"] = status
            if attempt is not None:
                self._delivery_status[event_id]["retry_count"] = attempt
            if error:
                self._delivery_status[event_id]["last_error"] = error
    
    async def acknowledge(self, event_id: UUID) -> None:
        """Acknowledge Event delivery."""
        if event_id in self._delivery_status:
            self._delivery_status[event_id]["acknowledged"] = True
            self._delivery_status[event_id]["acknowledged_at"] = datetime.utcnow().isoformat()
    
    async def get_pending_events(self) -> List[Event]:
        """Get pending Events for delivery."""
        pending = []
        for event_id, event in self._storage.items():
            status = self._delivery_status.get(event_id, {})
            if status.get("status") in ["created", "published", "retrying"]:
                pending.append(event)
        return pending
    
    async def count_by_company(self, company_id: UUID) -> int:
        """Count Events for a company."""
        return len([e for e in self._storage.values() if e.company_id == company_id])
    
    async def count_by_type(self, event_type: str) -> int:
        """Count Events by type."""
        return len([e for e in self._storage.values() if e.event_type == event_type])