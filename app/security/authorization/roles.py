# app/security/authorization/roles.py
"""
Roles - DOCUMENT 07 APP-041

Minimum platform roles:
- Viewer
- Analyst
- Manager
- Administrator
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Role:
    """Role definition."""
    name: str
    description: str
    permissions: Dict[str, List[str]]  # resource -> actions


class RoleManager:
    """
    Role Manager - Manages role definitions.
    """
    
    _instance = None
    _roles: Dict[str, Role] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._roles:
            self._init_default_roles()
    
    def _init_default_roles(self):
        """Initialize default platform roles."""
        
        # Viewer - Read-only access
        self._roles["viewer"] = Role(
            name="viewer",
            description="Read-only access",
            permissions={
                "datasets": ["view", "list"],
                "executions": ["view", "list"],
                "artifacts": ["view", "list"],
                "company": ["view"],
            }
        )
        
        # Analyst - Read and run analysis
        self._roles["analyst"] = Role(
            name="analyst",
            description="Read and run analysis",
            permissions={
                "datasets": ["view", "list", "upload", "validate"],
                "executions": ["view", "list", "create"],
                "artifacts": ["view", "list"],
                "objectives": ["view", "run"],
                "analysis": ["view", "run"],
                "company": ["view"],
            }
        )
        
        # Manager - Full access to own company
        self._roles["manager"] = Role(
            name="manager",
            description="Full access to own company",
            permissions={
                "datasets": ["view", "list", "upload", "validate", "approve"],
                "executions": ["view", "list", "create", "cancel"],
                "artifacts": ["view", "list", "publish"],
                "objectives": ["view", "run"],
                "analysis": ["view", "run"],
                "company": ["view", "update"],
                "users": ["view", "list"],
                "integrations": ["view", "sync"],
            }
        )
        
        # Administrator - Full platform access
        self._roles["administrator"] = Role(
            name="administrator",
            description="Full platform access",
            permissions={
                "*": ["*"],  # All resources, all actions
            }
        )
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self._roles.get(name.lower())
    
    def list_roles(self) -> List[str]:
        """List all role names."""
        return list(self._roles.keys())
    
    def has_permission(self, role_name: str, resource: str, action: str) -> bool:
        """Check if role has permission."""
        role = self.get_role(role_name)
        if not role:
            return False
        
        # Check wildcard permissions
        if "*" in role.permissions:
            if "*" in role.permissions["*"]:
                return True
            if action in role.permissions["*"]:
                return True
        
        # Check specific resource permissions
        if resource not in role.permissions:
            return False
        
        return action in role.permissions[resource]