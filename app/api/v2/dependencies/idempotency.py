"""Idempotency key dependency for V2 execution endpoints."""

from typing import Optional

from fastapi import Header


async def IdempotencyKey(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> Optional[str]:
    """Return the optional request idempotency key without changing request handling."""
    return idempotency_key
