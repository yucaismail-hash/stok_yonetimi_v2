# app/application/response/schemas.py
"""
Response Schemas - DOCUMENT 07 APP-005
Official response schema of the platform.

Every endpoint SHALL return the same response structure:
{
    success,
    message,
    data,
    metadata,
    trace_id,
    execution_id,
    timestamp
}
"""

from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ResponseMetadata(BaseModel):
    """Response metadata."""
    trace_id: str = Field(..., description="Trace ID for request tracking")
    request_id: str = Field(..., description="Unique request identifier")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for business flow")
    execution_id: Optional[UUID] = Field(None, description="Execution ID if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    duration_ms: Optional[float] = Field(None, description="Request duration in milliseconds")


class ErrorDetail(BaseModel):
    """Error detail."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field name if validation error")
    details: Optional[Any] = Field(None, description="Additional error details")


class APIResponse(BaseModel):
    """
    Standard API Response - DOCUMENT 07 APP-005
    
    Every endpoint SHALL return this structure.
    """
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="Response data")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Error details if any")
    metadata: ResponseMetadata = Field(..., description="Response metadata")
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None,
        }


class SuccessResponseBuilder:
    """Builder for success responses."""
    
    @staticmethod
    def build(
        data: Any,
        message: str = "Success",
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        execution_id: Optional[UUID] = None,
        duration_ms: Optional[float] = None,
    ) -> APIResponse:
        """Build a success response."""
        return APIResponse(
            success=True,
            message=message,
            data=data,
            errors=None,
            metadata=ResponseMetadata(
                trace_id=trace_id or "",
                request_id=request_id or "",
                correlation_id=correlation_id,
                execution_id=execution_id,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
            )
        )


class ErrorResponseBuilder:
    """Builder for error responses."""
    
    @staticmethod
    def build(
        message: str,
        errors: List[ErrorDetail],
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        execution_id: Optional[UUID] = None,
        duration_ms: Optional[float] = None,
    ) -> APIResponse:
        """Build an error response."""
        return APIResponse(
            success=False,
            message=message,
            data=None,
            errors=errors,
            metadata=ResponseMetadata(
                trace_id=trace_id or "",
                request_id=request_id or "",
                correlation_id=correlation_id,
                execution_id=execution_id,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
            )
        )