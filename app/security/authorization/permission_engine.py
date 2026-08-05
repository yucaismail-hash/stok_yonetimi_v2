# app/security/authorization/permission_engine.py
"""
Permission Engine - DOCUMENT 07 REVISION 03

Permission evaluation SHALL remain centralized.
AuthorizationService SHALL delegate permission decisions to PermissionEngine.

Future ABAC or Policy Based Security SHALL integrate here.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from app.security.authorization.roles import Role, RoleManager
from app.security.authorization.permissions import Permission, PermissionManager

logger = logging.getLogger(__name__)


class PermissionEngine:
    """
    Permission Engine - Centralized permission evaluation.
    
    Future ABAC or Policy Based Security SHALL integrate here.
    """
    
    def __init__(self):
        self.role_manager = RoleManager()
        self.permission_manager = PermissionManager()
    
    async def evaluate(
        self,
        user_id: UUID,
        company_id: UUID,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Evaluate permission for a user.
        
        Supports:
        - Role-based access control (RBAC)
        - Future Attribute-based access control (ABAC)
        - Future Policy-based access control
        """
        # Get user roles
        roles = await self._get_user_roles(user_id, company_id)
        
        # Check if any role has the required permission
        for role in roles:
            if await self._check_role_permission(role, resource, action):
                return True
        
        # Check direct permissions
        if await self._check_direct_permission(user_id, resource, action):
            return True
        
        # Future ABAC evaluation would go here
        if context and await self._evaluate_abac(user_id, resource, action, context):
            return True
        
        return False
    
    async def _get_user_roles(self, user_id: UUID, company_id: UUID) -> List[str]:
        """Get user roles."""
        # In production, this would fetch from database
        # Placeholder: return default roles
        return ["viewer"]
    
    async def _check_role_permission(self, role: str, resource: str, action: str) -> bool:
        """Check if role has permission."""
        role_obj = self.role_manager.get_role(role)
        if not role_obj:
            return False
        return resource in role_obj.permissions and action in role_obj.permissions[resource]
    
    async def _check_direct_permission(self, user_id: UUID, resource: str, action: str) -> bool:
        """Check direct user permissions."""
        # In production, this would check user-specific permissions
        return False
    
    async def _evaluate_abac(
        self,
        user_id: UUID,
        resource: str,
        action: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate Attribute-based access control.
        
        Future implementation for ABAC.
        """
        return False


class RBACEngine:
    """
    RBAC Engine - Role-based access control.
    
    Supports:
    - Viewer: Read-only access
    - Analyst: Read and run analysis
    - Manager: Full access to own company
    - Administrator: Full platform access
    """
    
    def __init__(self):
        self.role_manager = RoleManager()
    
    def has_permission(self, role: str, resource: str, action: str) -> bool:
        """Check if role has permission."""
        role_obj = self.role_manager.get_role(role)
        if not role_obj:
            return False
        
        if resource not in role_obj.permissions:
            return False
        
        return action in role_obj.permissions[resource]
    
    def get_permissions(self, role: str) -> Dict[str, List[str]]:
        """Get all permissions for a role."""
        role_obj = self.role_manager.get_role(role)
        if not role_obj:
            return {}
        return role_obj.permissions