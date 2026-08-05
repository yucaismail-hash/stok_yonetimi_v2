# app/security/authorization/__init__.py
"""Authorization - DOCUMENT 07 APP-041 / REVISION 03."""
from app.security.authorization.roles import Role, RoleManager
from app.security.authorization.permissions import Resource, Action, PermissionManager
from app.security.authorization.authorization_service import AuthorizationService
from app.security.authorization.permission_engine import PermissionEngine, RBACEngine

__all__ = [
    "Role",
    "RoleManager",
    "Resource",
    "Action",
    "PermissionManager",
    "AuthorizationService",
    "PermissionEngine",
    "RBACEngine",
]