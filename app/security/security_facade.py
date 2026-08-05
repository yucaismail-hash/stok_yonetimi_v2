# app/security/security_facade.py
"""
SecurityFacade - DOCUMENT 07 REVISION 01 / APP-040 / APP-041

The Application Layer SHALL communicate only with SecurityFacade.

SecurityFacade SHALL coordinate:
- Authentication
- Authorization
- Permission Validation
- Token Validation
- Company Isolation

API Layer SHALL NEVER communicate directly with authentication providers.
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging

from app.security.providers.jwt_provider import JWTProvider
from app.security.providers.api_key_provider import APIKeyProvider
from app.security.providers.service_token_provider import ServiceTokenProvider
from app.security.authorization.authorization_service import AuthorizationService
from app.security.authorization.permission_engine import PermissionEngine
from app.security.errors.error_catalog import ErrorCatalog

logger = logging.getLogger(__name__)


class SecurityFacade:
    """
    SecurityFacade - Central security coordination.
    
    API Layer SHALL NEVER communicate directly with authentication providers.
    """
    
    def __init__(self):
        self.jwt_provider = JWTProvider()
        self.api_key_provider = APIKeyProvider()
        self.service_token_provider = ServiceTokenProvider()
        self.authorization_service = AuthorizationService()
        self.permission_engine = PermissionEngine()
        self.error_catalog = ErrorCatalog()
    
    async def authenticate(self, token: str, token_type: str = "jwt") -> Dict[str, Any]:
        """
        Authenticate a request.
        
        Args:
            token: Authentication token
            token_type: jwt, api_key, service_token
        
        Returns:
            User information including user_id, company_id, roles
        """
        if token_type == "jwt":
            return await self.jwt_provider.validate(token)
        elif token_type == "api_key":
            return await self.api_key_provider.validate(token)
        elif token_type == "service_token":
            return await self.service_token_provider.validate(token)
        else:
            raise ValueError(f"Unknown token type: {token_type}")
    
    async def authorize(
        self,
        user_id: UUID,
        company_id: UUID,
        resource: str,
        action: str,
    ) -> bool:
        """
        Authorize a request.
        
        Checks:
        1. Role-based permissions
        2. Company isolation
        3. Resource-specific permissions
        """
        # Check company isolation
        if not await self.authorization_service.check_company_access(user_id, company_id):
            return False
        
        # Check permissions
        return await self.permission_engine.evaluate(
            user_id=user_id,
            company_id=company_id,
            resource=resource,
            action=action,
        )
    
    async def validate_request(
        self,
        token: str,
        token_type: str,
        company_id: UUID,
        resource: str,
        action: str,
    ) -> Dict[str, Any]:
        """
        Validate a complete request.
        
        Steps:
        1. Authenticate
        2. Authorize
        3. Return user context
        """
        # 1. Authenticate
        user_info = await self.authenticate(token, token_type)
        
        user_id = user_info.get("user_id")
        if not user_id:
            raise ValueError("Authentication failed: user_id not found")
        
        # 2. Authorize
        is_authorized = await self.authorize(
            user_id=user_id,
            company_id=company_id,
            resource=resource,
            action=action,
        )
        
        if not is_authorized:
            error = self.error_catalog.get("AUTH-010")
            raise PermissionError(f"{error.code}: {error.message}")
        
        # 3. Return user context
        return {
            "user_id": user_id,
            "company_id": company_id,
            "roles": user_info.get("roles", []),
            "permissions": user_info.get("permissions", []),
        }
    
    async def check_company_access(self, user_id: UUID, company_id: UUID) -> bool:
        """Check if user has access to company."""
        return await self.authorization_service.check_company_access(user_id, company_id)
    
    async def get_user_context(self, token: str, token_type: str = "jwt") -> Dict[str, Any]:
        """Get user context from token."""
        return await self.authenticate(token, token_type)