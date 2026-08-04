# app/repositories/user_repository.py
"""
User Repository
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.company import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity."""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(
            User.email == email,
            User.is_deleted == False
        ).first()

    def get_by_company(self, company_id: UUID) -> list:
        """Get all users of a company."""
        return self.db.query(User).filter(
            User.company_id == company_id,
            User.is_deleted == False
        ).all()

    def get_by_role(self, role: str, company_id: Optional[UUID] = None) -> list:
        """Get users by role."""
        query = self.db.query(User).filter(
            User.role == role,
            User.is_deleted == False
        )
        if company_id:
            query = query.filter(User.company_id == company_id)
        return query.all()

    def update_balance(self, user_id: UUID, amount: int) -> Optional[User]:
        """Update user token balance."""
        user = self.get_by_id(user_id)
        if user:
            user.token_balance += amount
            self.db.flush()
        return user