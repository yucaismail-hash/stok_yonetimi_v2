# app/security/providers/jwt_provider.py
"""
JWT Provider - DOCUMENT 07 REVISION 02

JWT Authentication Provider.
"""

from typing import Dict, Any
from uuid import UUID
import jwt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class JWTProvider:
    """
    JWT Authentication Provider.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.secret = self.config.get("secret", "your-secret-key-change-in-production")
        self.algorithm = self.config.get("algorithm", "HS256")
        self.expiry_minutes = self.config.get("expiry_minutes", 60)
    
    async def validate(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token.
        
        Returns:
            User information
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            
            return {
                "user_id": UUID(payload.get("sub")),
                "company_id": UUID(payload.get("company_id")),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "exp": payload.get("exp"),
                "issued_at": payload.get("iat"),
            }
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    async def create_token(
        self,
        user_id: UUID,
        company_id: UUID,
        roles: list[str] = None,
        permissions: list[str] = None,
    ) -> str:
        """
        Create JWT token.
        """
        payload = {
            "sub": str(user_id),
            "company_id": str(company_id),
            "roles": roles or [],
            "permissions": permissions or [],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=self.expiry_minutes),
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)