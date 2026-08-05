# app/api/v2/schemas/base_response.py
"""
Base Response Schema - DOCUMENT 07 APP-019 / REVISION 04

All response schemas SHALL inherit from this base model.
This guarantees a consistent API contract throughout the platform.

Every endpoint SHALL return the official platform response schema:
{
    success,
    message,
    data,
    metadata,
    request_id,
    trace_id,
    correlation_id,
    execution_id,
    timestamp
}
"""

from typing import Optional, Any, Dict, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ResponseMetadata(BaseModel):
    """Response metadata."""
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    trace_id: Optional[str] = Field(None, description="Trace ID for request tracking")
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


class BaseResponse(BaseModel):
    """
    Base Response Schema - All responses SHALL inherit from this.
    
    Every endpoint SHALL return this structure.
    """
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="Response data")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Error details if any")
    metadata: ResponseMetadata = Field(..., description="Response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Success",
                "data": {"execution_id": "123e4567-e89b-12d3-a456-426614174000"},
                "errors": None,
                "metadata": {
                    "request_id": "req_12345",
                    "trace_id": "trace_12345",
                    "correlation_id": "corr_12345",
                    "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "duration_ms": 150.5
                }
            }
        }


class ExecutionResponse(BaseResponse):
    """
    Execution Response Schema.
    """
    
    data: Optional[Dict[str, Any]] = Field(None, description="Execution data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Execution started successfully",
                "data": {
                    "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "pending",
                    "message": "Execution started"
                },
                "errors": None,
                "metadata": {
                    "request_id": "req_12345",
                    "trace_id": "trace_12345",
                    "correlation_id": "corr_12345",
                    "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "duration_ms": 150.5
                }
            }
        }


class ArtifactResponse(BaseResponse):
    """
    Artifact Response Schema.
    """
    
    data: Optional[Dict[str, Any]] = Field(None, description="Artifact data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Artifact retrieved successfully",
                "data": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "artifact_type": "analysis_narrative",
                    "artifact_version": 1,
                    "content": {...}
                },
                "errors": None,
                "metadata": {
                    "request_id": "req_12345",
                    "trace_id": "trace_12345",
                    "correlation_id": "corr_12345",
                    "execution_id": "123e4567-e89b-12d3-a456-426614174001",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "duration_ms": 150.5
                }
            }
        }