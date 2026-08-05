# app/api/v2/middleware/idempotency.py
"""
Idempotency Middleware - DOCUMENT 07 APP-024

Execution endpoints SHOULD support Idempotency-Key.
Repeated requests SHALL NOT create duplicate executions.
"""

from typing import Optional, Dict, Any
import hashlib
import json
from datetime import datetime, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.application.response.response_builder import ResponseBuilder
from app.application.models.trace_context import TraceContextHolder


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency Middleware - Supports Idempotency-Key header.
    
    Repeated requests with same Idempotency-Key SHALL NOT
    create duplicate executions.
    """
    
    # In-memory cache for idempotency keys (should be replaced with Redis in production)
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_ttl: int = 3600  # 1 hour
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with idempotency check.
        """
        # Only check idempotency for POST requests
        if request.method != "POST":
            return await call_next(request)
        
        idempotency_key = request.headers.get("Idempotency-Key")
        
        # If no idempotency key, proceed normally
        if not idempotency_key:
            return await call_next(request)
        
        # Check if we have a cached response for this key
        cached_response = self._get_cached_response(idempotency_key)
        if cached_response:
            return JSONResponse(
                content=cached_response,
                status_code=202  # Accepted
            )
        
        # Process the request
        response = await call_next(request)
        
        # Cache the response for future idempotent requests
        if response.status_code in [200, 201, 202]:
            self._cache_response(idempotency_key, response)
        
        return response
    
    def _get_cached_response(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response for idempotency key."""
        cache_entry = self._cache.get(key)
        if not cache_entry:
            return None
        
        # Check if cache entry has expired
        cached_at = cache_entry.get("cached_at")
        if cached_at:
            cached_time = datetime.fromisoformat(cached_at)
            if datetime.utcnow() - cached_time > timedelta(seconds=self._cache_ttl):
                del self._cache[key]
                return None
        
        return cache_entry.get("response")
    
    def _cache_response(self, key: str, response: Response) -> None:
        """Cache response for idempotency key."""
        # Extract response content
        content = None
        if hasattr(response, "body"):
            try:
                content = json.loads(response.body)
            except:
                pass
        
        self._cache[key] = {
            "response": content,
            "cached_at": datetime.utcnow().isoformat(),
            "status_code": response.status_code,
        }