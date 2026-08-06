# app/security/errors/error_handler.py
"""
Error Handler - DOCUMENT 07 APP-043 / REVISION 05

Standardizes error handling for the platform.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.security.errors.error_catalog import ErrorCatalog, ErrorCategory
from app.api.v2.schemas.base_response import BaseResponse, ErrorDetail, ResponseMetadata


class ErrorHandler:
    """
    Error Handler - Standardizes error responses.
    
    Every error SHALL contain:
    - error_code
    - error_message
    - category
    - details
    - trace_id
    """
    
    def __init__(self):
        self.catalog = ErrorCatalog()
    
    def create_error_response(
        self,
        code: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> JSONResponse:
        """
        Create a standardized error response.
        """
        error_def = self.catalog.get(code)
        
        if not error_def:
            # Fallback to unknown error
            error_def = self.catalog.get("SYS-001")
        
        error_message = message or error_def.message
        
        error_detail = ErrorDetail(
            code=code,
            message=error_message,
            details=details or {},
        )
        
        response = BaseResponse(
            success=False,
            message=error_message,
            data=None,
            errors=[error_detail],
            metadata=ResponseMetadata(
                trace_id=trace_id or "",
                request_id=request_id or "",
                timestamp=datetime.utcnow(),
            )
        )
        
        return JSONResponse(
            status_code=error_def.http_status,
            content=response.dict(exclude_none=True),
        )
    
    def handle_exception(
        self,
        request: Request,
        exc: Exception,
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """
        Handle an exception and return a standardized error response.
        """
        # Determine error code based on exception type
        code = self._get_error_code(exc)
        
        return self.create_error_response(
            code=code,
            message=str(exc),
            details={"exception_type": type(exc).__name__},
            trace_id=trace_id,
            request_id=request.headers.get("X-Request-ID"),
        )
    
    def _get_error_code(self, exc: Exception) -> str:
        """Get error code for exception."""
        if isinstance(exc, ValueError):
            return "DATA-002"
        elif isinstance(exc, PermissionError):
            return "AUTH-010"
        elif isinstance(exc, FileNotFoundError):
            return "DATA-001"
        else:
            return "SYS-001"
