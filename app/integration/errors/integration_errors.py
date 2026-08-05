# app/integration/errors/integration_errors.py
"""
Integration Errors - DOCUMENT 07 APP-031 / REVISION 08

Standard Integration Error Hierarchy.

Every adapter SHALL use the same error model.
Internal implementation details SHALL NEVER be exposed.
"""

from typing import Optional, Dict, Any


class IntegrationError(Exception):
    """Base Integration Error."""
    
    def __init__(
        self,
        message: str,
        code: str = "integration_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class ConnectionError(IntegrationError):
    """Connection Error - Failed to connect to external system."""
    
    def __init__(
        self,
        message: str = "Failed to connect to external system",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="connection_error", details=details)


class AuthenticationError(IntegrationError):
    """Authentication Error - Failed to authenticate with external system."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="authentication_error", details=details)


class ValidationError(IntegrationError):
    """Validation Error - Payload validation failed."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="validation_error", details=details)


class TransformationError(IntegrationError):
    """Transformation Error - Data transformation failed."""
    
    def __init__(
        self,
        message: str = "Data transformation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="transformation_error", details=details)


class MappingError(IntegrationError):
    """Mapping Error - Field mapping failed."""
    
    def __init__(
        self,
        message: str = "Field mapping failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="mapping_error", details=details)


class SynchronizationError(IntegrationError):
    """Synchronization Error - Sync operation failed."""
    
    def __init__(
        self,
        message: str = "Synchronization failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="synchronization_error", details=details)


class TimeoutError(IntegrationError):
    """Timeout Error - Operation timed out."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="timeout_error", details=details)


class RetryLimitExceeded(IntegrationError):
    """Retry Limit Exceeded - Maximum retry attempts exceeded."""
    
    def __init__(
        self,
        message: str = "Maximum retry attempts exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code="retry_limit_exceeded", details=details)