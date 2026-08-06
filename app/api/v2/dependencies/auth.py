"""Authentication dependencies for V2 endpoints."""

from uuid import UUID

from fastapi import Depends

from app.auth import get_current_user


async def get_user_id(current_user=Depends(get_current_user)) -> UUID:
    """Return the authenticated user's identifier using the existing auth dependency."""
    return current_user.id
