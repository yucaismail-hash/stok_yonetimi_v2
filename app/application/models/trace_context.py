# app/application/models/trace_context.py
"""
Trace Context Model - DOCUMENT 07 APP-007
Standardized platform identifiers for traceability.

Every request SHALL contain:
- request_id: Unique HTTP request identifier
- trace_id: Tracks the request across platform layers
- correlation_id: Groups related operations belonging to the same business flow
- execution_id: Represents one analytical execution

These identifiers SHALL remain immutable during execution.
"""

from typing import Optional
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TraceContext:
    """
    Trace Context - Immutable identifiers for request tracking.
    
    DOCUMENT 07 APP-007: Traceability Standard
    """
    
    request_id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    execution_id: Optional[UUID] = None
    
    user_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    started_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "company_id": str(self.company_id) if self.company_id else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }
    
    def with_execution_id(self, execution_id: UUID) -> "TraceContext":
        """Create a new context with execution_id set."""
        return TraceContext(
            request_id=self.request_id,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
            execution_id=execution_id,
            user_id=self.user_id,
            company_id=self.company_id,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            started_at=self.started_at,
        )
    
    def with_correlation_id(self, correlation_id: str) -> "TraceContext":
        """Create a new context with correlation_id set."""
        return TraceContext(
            request_id=self.request_id,
            trace_id=self.trace_id,
            correlation_id=correlation_id,
            execution_id=self.execution_id,
            user_id=self.user_id,
            company_id=self.company_id,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            started_at=self.started_at,
        )


class TraceContextHolder:
    """
    Thread-local holder for TraceContext.
    """
    
    _context: Optional[TraceContext] = None
    
    @classmethod
    def set_context(cls, context: TraceContext) -> None:
        """Set the current trace context."""
        cls._context = context
    
    @classmethod
    def get_context(cls) -> Optional[TraceContext]:
        """Get the current trace context."""
        return cls._context
    
    @classmethod
    def clear(cls) -> None:
        """Clear the current trace context."""
        cls._context = None
    
    @classmethod
    def get_request_id(cls) -> Optional[str]:
        """Get current request_id."""
        if cls._context:
            return cls._context.request_id
        return None
    
    @classmethod
    def get_trace_id(cls) -> Optional[str]:
        """Get current trace_id."""
        if cls._context:
            return cls._context.trace_id
        return None
    
    @classmethod
    def get_execution_id(cls) -> Optional[UUID]:
        """Get current execution_id."""
        if cls._context:
            return cls._context.execution_id
        return None