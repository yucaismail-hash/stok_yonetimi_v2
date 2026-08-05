# app/api/v2/middleware/trace.py
"""
Trace Middleware - DOCUMENT 07 APP-007
Adds traceability to every request.

Every request SHALL receive:
- request_id
- trace_id
- correlation_id
"""

from typing import Optional
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.application.models.trace_context import TraceContext, TraceContextHolder


class TraceMiddleware(BaseHTTPMiddleware):
    """
    Trace Middleware - Adds trace context to every request.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with trace context.
        """
        # Get or create trace identifiers
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        trace_id = request.headers.get("X-Trace-ID", str(uuid4()))
        correlation_id = request.headers.get("X-Correlation-ID")
        
        # Create trace context
        context = TraceContext(
            request_id=request_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        
        # Set context
        TraceContextHolder.set_context(context)
        
        # Add headers to request state
        request.state.trace_context = context
        
        # Process request
        response = await call_next(request)
        
        # Add trace headers to response
        response.headers["X-Request-ID"] = context.request_id
        response.headers["X-Trace-ID"] = context.trace_id
        if context.correlation_id:
            response.headers["X-Correlation-ID"] = context.correlation_id
        if context.execution_id:
            response.headers["X-Execution-ID"] = str(context.execution_id)
        
        # Clear context
        TraceContextHolder.clear()
        
        return response