# app/events/models/event.py
"""
Event Model - DOCUMENT 07 APP-032

Every Event SHALL contain:
- event_id
- event_type
- event_version
- company_id
- execution_id
- artifact_id
- timestamp
- payload
- metadata

Every Event SHALL use the same schema.
Events SHALL represent business facts.
Events SHALL remain immutable.
"""

from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class EventCategory(str, Enum):
    """Event Categories."""
    DATASET = "dataset"
    EXECUTION = "execution"
    ARTIFACT = "artifact"
    LEARNING = "learning"
    INTEGRATION = "integration"


class EventStatus(str, Enum):
    """Event Status."""
    CREATED = "created"
    PUBLISHED = "published"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    ACKNOWLEDGED = "acknowledged"
    ARCHIVED = "archived"


@dataclass
class Event:
    """
    Base Event - DOCUMENT 07 APP-032
    
    Events SHALL represent Business Facts.
    Events SHALL NOT represent Commands, Requests, or Queries.
    Events SHALL remain immutable.
    """
    
    # Identifiers
    event_id: UUID = field(default_factory=uuid4)
    event_type: str
    event_version: str = "1.0"
    
    # Core
    company_id: UUID
    execution_id: Optional[UUID] = None
    artifact_id: Optional[UUID] = None
    
    # Payload
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Traceability
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Status
    status: EventStatus = EventStatus.CREATED
    
    # Publisher
    source_component: Optional[str] = None
    publisher: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "event_version": self.event_version,
            "company_id": str(self.company_id),
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "artifact_id": str(self.artifact_id) if self.artifact_id else None,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "status": self.status.value if self.status else None,
            "source_component": self.source_component,
            "publisher": self.publisher,
        }
    
    def with_status(self, status: EventStatus) -> "Event":
        """Create a new event with updated status."""
        return Event(
            event_id=self.event_id,
            event_type=self.event_type,
            event_version=self.event_version,
            company_id=self.company_id,
            execution_id=self.execution_id,
            artifact_id=self.artifact_id,
            payload=self.payload,
            metadata=self.metadata,
            timestamp=self.timestamp,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
            request_id=self.request_id,
            status=status,
            source_component=self.source_component,
            publisher=self.publisher,
        )