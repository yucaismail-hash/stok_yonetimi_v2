# app/security/errors/error_catalog.py
"""
Error Catalog - DOCUMENT 07 APP-043 / REVISION 05

The platform SHALL maintain one official Error Catalog.
Every module SHALL reference this catalog.
Duplicate error definitions SHALL NOT exist.
"""

from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass


class ErrorCategory(str, Enum):
    """Error Categories."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATASET = "dataset"
    EXECUTION = "execution"
    ARTIFACT = "artifact"
    INTEGRATION = "integration"
    SYSTEM = "system"
    VALIDATION = "validation"


@dataclass
class ErrorDefinition:
    """Error definition."""
    code: str
    message: str
    category: ErrorCategory
    http_status: int
    description: Optional[str] = None


class ErrorCatalog:
    """
    Error Catalog - Central registry for all errors.
    
    Every module SHALL reference this catalog.
    Duplicate error definitions SHALL NOT exist.
    """
    
    _instance = None
    _errors: Dict[str, ErrorDefinition] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, error: ErrorDefinition) -> None:
        """Register an error definition."""
        if error.code in self._errors:
            raise ValueError(f"Error code already registered: {error.code}")
        self._errors[error.code] = error
    
    def get(self, code: str) -> Optional[ErrorDefinition]:
        """Get error definition by code."""
        return self._errors.get(code)
    
    def get_by_category(self, category: ErrorCategory) -> list:
        """Get errors by category."""
        return [e for e in self._errors.values() if e.category == category]
    
    def list_all(self) -> list:
        """List all error definitions."""
        return list(self._errors.values())


# Initialize error catalog
_error_catalog = ErrorCatalog()

# Register default errors
_error_catalog.register(ErrorDefinition(
    code="AUTH-001",
    message="Invalid Authentication Token",
    category=ErrorCategory.AUTHENTICATION,
    http_status=401,
    description="The provided authentication token is invalid or malformed."
))

_error_catalog.register(ErrorDefinition(
    code="AUTH-002",
    message="Expired Token",
    category=ErrorCategory.AUTHENTICATION,
    http_status=401,
    description="The authentication token has expired."
))

_error_catalog.register(ErrorDefinition(
    code="AUTH-003",
    message="Invalid API Key",
    category=ErrorCategory.AUTHENTICATION,
    http_status=401,
    description="The provided API key is invalid."
))

_error_catalog.register(ErrorDefinition(
    code="AUTH-010",
    message="Insufficient Permissions",
    category=ErrorCategory.AUTHORIZATION,
    http_status=403,
    description="User does not have sufficient permissions."
))

_error_catalog.register(ErrorDefinition(
    code="AUTH-011",
    message="Cross-Company Access Denied",
    category=ErrorCategory.AUTHORIZATION,
    http_status=403,
    description="Access to resources from another company is not allowed."
))

_error_catalog.register(ErrorDefinition(
    code="DATA-001",
    message="Dataset Not Found",
    category=ErrorCategory.DATASET,
    http_status=404,
    description="The requested dataset could not be found."
))

_error_catalog.register(ErrorDefinition(
    code="DATA-002",
    message="Dataset Validation Failed",
    category=ErrorCategory.DATASET,
    http_status=422,
    description="Dataset validation failed. Check errors for details."
))

_error_catalog.register(ErrorDefinition(
    code="EXEC-001",
    message="Execution Not Found",
    category=ErrorCategory.EXECUTION,
    http_status=404,
    description="The requested execution could not be found."
))

_error_catalog.register(ErrorDefinition(
    code="EXEC-002",
    message="Execution Failed",
    category=ErrorCategory.EXECUTION,
    http_status=500,
    description="The execution failed. Check logs for details."
))

_error_catalog.register(ErrorDefinition(
    code="ART-001",
    message="Artifact Not Found",
    category=ErrorCategory.ARTIFACT,
    http_status=404,
    description="The requested AI Artifact could not be found."
))

_error_catalog.register(ErrorDefinition(
    code="ART-002",
    message="Artifact Version Not Available",
    category=ErrorCategory.ARTIFACT,
    http_status=404,
    description="The requested artifact version is not available."
))

_error_catalog.register(ErrorDefinition(
    code="INT-001",
    message="Integration Failure",
    category=ErrorCategory.INTEGRATION,
    http_status=500,
    description="Integration operation failed."
))

_error_catalog.register(ErrorDefinition(
    code="SYS-001",
    message="Unexpected Internal Error",
    category=ErrorCategory.SYSTEM,
    http_status=500,
    description="An unexpected internal error occurred."
))

_error_catalog.register(ErrorDefinition(
    code="SYS-002",
    message="Service Unavailable",
    category=ErrorCategory.SYSTEM,
    http_status=503,
    description="The service is temporarily unavailable."
))

_error_catalog.register(ErrorDefinition(
    code="SYS-003",
    message="Rate Limit Exceeded",
    category=ErrorCategory.SYSTEM,
    http_status=429,
    description="Rate limit exceeded. Please wait and retry."
))