# app/security/authorization/permissions.py
"""
Permissions - DOCUMENT 07 APP-041

Resource and action definitions for authorization.
"""

from typing import List, Dict, Optional


class Resource:
    """Resource types."""
    DATASETS = "datasets"
    EXECUTIONS = "executions"
    ARTIFACTS = "artifacts"
    OBJECTIVES = "objectives"
    ANALYSIS = "analysis"
    COMPANY = "company"
    USERS = "users"
    INTEGRATIONS = "integrations"


class Action:
    """Action types."""
    VIEW = "view"
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    UPLOAD = "upload"
    VALIDATE = "validate"
    APPROVE = "approve"
    RUN = "run"
    CANCEL = "cancel"
    PUBLISH = "publish"
    SYNC = "sync"


class PermissionManager:
    """
    Permission Manager - Manages permission definitions.
    """
    
    _instance = None
    _permissions: Dict[str, Dict[str, List[str]]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._permissions:
            self._init_default_permissions()
    
    def _init_default_permissions(self):
        """Initialize default permission definitions."""
        self._permissions = {
            Resource.DATASETS: {
                Action.VIEW: "View dataset details",
                Action.LIST: "List datasets",
                Action.UPLOAD: "Upload dataset",
                Action.VALIDATE: "Validate dataset",
                Action.APPROVE: "Approve dataset",
            },
            Resource.EXECUTIONS: {
                Action.VIEW: "View execution details",
                Action.LIST: "List executions",
                Action.CREATE: "Create execution",
                Action.CANCEL: "Cancel execution",
            },
            Resource.ARTIFACTS: {
                Action.VIEW: "View artifact details",
                Action.LIST: "List artifacts",
                Action.PUBLISH: "Publish artifact",
            },
            Resource.OBJECTIVES: {
                Action.VIEW: "View objectives",
                Action.RUN: "Run business objective",
            },
            Resource.ANALYSIS: {
                Action.VIEW: "View analysis",
                Action.RUN: "Run analysis",
            },
            Resource.COMPANY: {
                Action.VIEW: "View company",
                Action.UPDATE: "Update company",
            },
            Resource.USERS: {
                Action.VIEW: "View users",
                Action.LIST: "List users",
            },
            Resource.INTEGRATIONS: {
                Action.VIEW: "View integrations",
                Action.SYNC: "Synchronize integration",
            },
        }
    
    def get_permission(self, resource: str, action: str) -> Optional[str]:
        """Get permission description."""
        if resource in self._permissions:
            return self._permissions[resource].get(action)
        return None
    
    def get_actions(self, resource: str) -> List[str]:
        """Get all actions for a resource."""
        if resource in self._permissions:
            return list(self._permissions[resource].keys())
        return []
    
    def list_resources(self) -> List[str]:
        """List all resources."""
        return list(self._permissions.keys())