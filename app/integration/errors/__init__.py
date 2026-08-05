# app/integration/errors/__init__.py
"""
Integration Errors - DOCUMENT 07 APP-031 / REVISION 08
"""

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
from app.integration.errors.error_handler import ErrorHandler

__all__ = [
    "IntegrationError",
    "ConnectionError",
    "AuthenticationError",
    "ValidationError",
    "TransformationError",
    "MappingError",
    "SynchronizationError",
    "TimeoutError",
    "RetryLimitExceeded",
    "ErrorHandler",
]