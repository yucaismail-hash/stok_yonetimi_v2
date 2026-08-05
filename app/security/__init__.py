# app/security/__init__.py
"""
Security - DOCUMENT 07 PART 06

Security SHALL remain platform wide.
Authentication providers, Authorization, Permissions,
API Contracts, Error Catalog, Rate Limiting, Compatibility
SHALL remain reusable services.
"""

from app.security.security_facade import SecurityFacade
from app.security.providers.jwt_provider import JWTProvider
from app.security.providers.api_key_provider import APIKeyProvider
from app.security.providers.service_token_provider import ServiceTokenProvider
from app.security.authorization.roles import Role, RoleManager
from app.security.authorization.permissions import Resource, Action, PermissionManager
from app.security.authorization.authorization_service import AuthorizationService
from app.security.authorization.permission_engine import PermissionEngine, RBACEngine
from app.security.errors.error_catalog import ErrorCatalog, ErrorDefinition, ErrorCategory
from app.security.errors.error_handler import ErrorHandler

__all__ = [
    "SecurityFacade",
    "JWTProvider",
    "APIKeyProvider",
    "ServiceTokenProvider",
    "Role",
    "RoleManager",
    "Resource",
    "Action",
    "PermissionManager",
    "AuthorizationService",
    "PermissionEngine",
    "RBACEngine",
    "ErrorCatalog",
    "ErrorDefinition",
    "ErrorCategory",
    "ErrorHandler",
]