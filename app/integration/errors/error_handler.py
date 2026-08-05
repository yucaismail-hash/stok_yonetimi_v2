# app/integration/errors/error_handler.py
"""
Integration Error Handler - DOCUMENT 07 APP-031 / REVISION 08

Standardizes error handling for all integration operations.
"""

from typing import Optional, Dict, Any
import logging

from app.integration.errors.integration_errors import (
    IntegrationError,
    ConnectionError,
    AuthenticationError,
    ValidationError,
    TransformationError,
    MappingError,
    SynchronizationError,
    TimeoutError,
    RetryLimitExceeded,
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Integration Error Handler.
    
    Standardizes error handling and ensures internal implementation details
    are NEVER exposed to external systems.
    """
    
    @classmethod
    def handle(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an integration error.
        
        Returns a standardized error response.
        Internal implementation details SHALL NEVER be exposed.
        """
        context = context or {}
        
        if isinstance(error, IntegrationError):
            return cls._handle_integration_error(error, context)
        else:
            return cls._handle_unexpected_error(error, context)
    
    @classmethod
    def _handle_integration_error(
        cls,
        error: IntegrationError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle known integration error."""
        logger.warning(
            f"Integration error: {error.code} - {error.message}",
            extra={
                "code": error.code,
                "details": error.details,
                "context": context,
            }
        )
        
        return {
            "success": False,
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            },
            "context": context,
        }
    
    @classmethod
    def _handle_unexpected_error(
        cls,
        error: Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle unexpected error."""
        logger.error(
            f"Unexpected integration error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "context": context,
            },
            exc_info=True,
        )
        
        return {
            "success": False,
            "error": {
                "code": "unexpected_error",
                "message": "An unexpected error occurred",
                "details": {
                    "error_type": type(error).__name__,
                },
            },
            "context": context,
        }
    
    @classmethod
    def is_retryable(cls, error: Exception) -> bool:
        """Check if error is retryable."""
        if isinstance(error, IntegrationError):
            return error.code in [
                "connection_error",
                "timeout_error",
                "synchronization_error",
            ]
        return False
    
    @classmethod
    def get_retry_delay(cls, error: Exception, attempt: int) -> int:
        """Get retry delay in seconds."""
        base_delay = 5
        max_delay = 60
        
        # Exponential backoff
        delay = min(base_delay * (2 ** attempt), max_delay)
        
        # Add jitter
        import random
        delay = delay + random.uniform(0, 1)
        
        return int(delay)