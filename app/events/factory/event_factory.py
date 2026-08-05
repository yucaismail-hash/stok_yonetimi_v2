# app/events/factory/event_factory.py
"""
Event Factory - DOCUMENT 07 REVISION 02

Every Event SHALL be created only through Event Factory.
No component SHALL instantiate Event objects directly.

Event Factory SHALL automatically populate:
- Event ID
- Event Version
- Schema Version
- Timestamp
- Metadata
- Correlation Information

This guarantees immutable and standardized Events.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.events.models.event import Event, EventStatus
from app.events.registry.event_registry import EventRegistry


class EventFactory:
    """
    Event Factory - Creates Events.
    
    Every Event SHALL be created only through this factory.
    Automatically populates standard fields.
    """
    
    def __init__(self):
        self.registry = EventRegistry()
    
    def create(
        self,
        event_type: str,
        company_id: UUID,
        payload: Dict[str, Any],
        execution_id: Optional[UUID] = None,
        artifact_id: Optional[UUID] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        source_component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        Create an Event.
        
        Args:
            event_type: Registered event type
            company_id: Company ID
            payload: Event payload (business facts)
            execution_id: Optional execution ID
            artifact_id: Optional artifact ID
            trace_id: Optional trace ID
            correlation_id: Optional correlation ID
            request_id: Optional request ID
            source_component: Source component name
            metadata: Additional metadata
        
        Returns:
            Event: Immutable Event object
        
        Raises:
            ValueError: If event_type is not registered
        """
        # Validate event_type is registered
        if not self.registry.is_registered(event_type):
            raise ValueError(f"Event type '{event_type}' is not registered")
        
        # Get event version from registry
        event_version = self.registry.get_version(event_type) or "1.0"
        
        # Build metadata
        event_metadata = {
            "source_component": source_component,
            "schema_version": "1.0",
            "producer_version": "1.0",
            **(metadata or {}),
        }
        
        # Create Event
        event = Event(
            event_type=event_type,
            event_version=event_version,
            company_id=company_id,
            execution_id=execution_id,
            artifact_id=artifact_id,
            payload=payload,
            metadata=event_metadata,
            timestamp=datetime.utcnow(),
            trace_id=trace_id,
            correlation_id=correlation_id,
            request_id=request_id,
            status=EventStatus.CREATED,
            source_component=source_component,
        )
        
        return event
    
    def create_dataset_uploaded(
        self,
        company_id: UUID,
        dataset_id: UUID,
        user_id: UUID,
        source_type: str,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """Create Dataset Uploaded event."""
        return self.create(
            event_type="dataset.uploaded",
            company_id=company_id,
            payload={
                "dataset_id": str(dataset_id),
                "user_id": str(user_id),
                "source_type": source_type,
                "uploaded_at": datetime.utcnow().isoformat(),
            },
            trace_id=trace_id,
            correlation_id=correlation_id,
            source_component="dataset_service",
        )
    
    def create_execution_started(
        self,
        company_id: UUID,
        execution_id: UUID,
        dataset_id: UUID,
        objective_type: str,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """Create Execution Started event."""
        return self.create(
            event_type="execution.started",
            company_id=company_id,
            payload={
                "execution_id": str(execution_id),
                "dataset_id": str(dataset_id),
                "objective_type": objective_type,
                "started_at": datetime.utcnow().isoformat(),
            },
            execution_id=execution_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            source_component="workflow_engine",
        )
    
    def create_execution_completed(
        self,
        company_id: UUID,
        execution_id: UUID,
        artifact_id: UUID,
        status: str,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """Create Execution Completed event."""
        return self.create(
            event_type="execution.completed",
            company_id=company_id,
            payload={
                "execution_id": str(execution_id),
                "artifact_id": str(artifact_id),
                "status": status,
                "completed_at": datetime.utcnow().isoformat(),
            },
            execution_id=execution_id,
            artifact_id=artifact_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            source_component="decision_intelligence",
        )
    
    def create_artifact_created(
        self,
        company_id: UUID,
        artifact_id: UUID,
        execution_id: UUID,
        artifact_type: str,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """Create Artifact Created event."""
        return self.create(
            event_type="artifact.created",
            company_id=company_id,
            payload={
                "artifact_id": str(artifact_id),
                "execution_id": str(execution_id),
                "artifact_type": artifact_type,
                "created_at": datetime.utcnow().isoformat(),
            },
            execution_id=execution_id,
            artifact_id=artifact_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            source_component="artifact_persistence_service",
        )