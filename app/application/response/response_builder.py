# app/application/response/response_builder.py
"""
Response Builder - DOCUMENT 07 REVISION 05
Standard response generation.

Middleware SHALL remain responsible only for:
- Authentication
- Tracing
- Request lifecycle

ResponseBuilder SHALL become responsible for:
- Standard response generation
- Metadata
- Execution identifiers
- Error formatting
- Response schema consistency
"""

from typing import Optional, Any, List, Dict, Union
from uuid import UUID
from datetime import datetime
import time

from app.application.models.trace_context import TraceContextHolder
from app.application.response.schemas import (
    APIResponse,
    SuccessResponseBuilder,
    ErrorResponseBuilder,
    ErrorDetail,
)


class ResponseBuilder:
    """
    Standard response builder for the platform.
    
    DOCUMENT 07 APP-005 / REVISION 05
    """
    
    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str = "Success",
        execution_id: Optional[UUID] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> APIResponse:
        """
        Build a success response.
        """
        context = TraceContextHolder.get_context()
        
        return SuccessResponseBuilder.build(
            data=data,
            message=message,
            trace_id=context.trace_id if context else None,
            request_id=context.request_id if context else None,
            correlation_id=context.correlation_id if context else None,
            execution_id=execution_id or (context.execution_id if context else None),
            duration_ms=duration_ms,
        )
    
    @classmethod
    def error(
        cls,
        message: str = "An error occurred",
        errors: Optional[List[Union[ErrorDetail, Dict[str, Any]]]] = None,
        execution_id: Optional[UUID] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> APIResponse:
        """
        Build an error response.
        """
        context = TraceContextHolder.get_context()
        
        # Convert dict errors to ErrorDetail
        error_objects = []
        if errors:
            for error in errors:
                if isinstance(error, dict):
                    error_objects.append(ErrorDetail(**error))
                elif isinstance(error, ErrorDetail):
                    error_objects.append(error)
        
        return ErrorResponseBuilder.build(
            message=message,
            errors=error_objects,
            trace_id=context.trace_id if context else None,
            request_id=context.request_id if context else None,
            correlation_id=context.correlation_id if context else None,
            execution_id=execution_id or (context.execution_id if context else None),
            duration_ms=duration_ms,
        )
    
    @classmethod
    def validation_error(
        cls,
        errors: List[Dict[str, Any]],
        message: str = "Validation failed",
        **kwargs
    ) -> APIResponse:
        """
        Build a validation error response.
        """
        error_details = []
        for error in errors:
            error_details.append(ErrorDetail(
                code="validation_error",
                message=error.get("message", "Invalid field"),
                field=error.get("field"),
                details=error.get("details"),
            ))
        
        return cls.error(message=message, errors=error_details, **kwargs)
    
    @classmethod
    def not_found(
        cls,
        resource: str = "Resource",
        **kwargs
    ) -> APIResponse:
        """
        Build a not found error response.
        """
        return cls.error(
            message=f"{resource} not found",
            errors=[ErrorDetail(
                code="not_found",
                message=f"{resource} not found",
            )],
            **kwargs
        )
    
    @classmethod
    def unauthorized(
        cls,
        message: str = "Unauthorized",
        **kwargs
    ) -> APIResponse:
        """
        Build an unauthorized error response.
        """
        return cls.error(
            message=message,
            errors=[ErrorDetail(
                code="unauthorized",
                message="Authentication required",
            )],
            **kwargs
        )
    
    @classmethod
    def forbidden(
        cls,
        message: str = "Forbidden",
        **kwargs
    ) -> APIResponse:
        """
        Build a forbidden error response.
        """
        return cls.error(
            message=message,
            errors=[ErrorDetail(
                code="forbidden",
                message="Insufficient permissions",
            )],
            **kwargs
        )