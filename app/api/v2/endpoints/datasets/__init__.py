# app/api/v2/endpoints/datasets/__init__.py
"""Dataset endpoints - CRUD operations."""
from app.api.v2.endpoints.datasets.create import router as create_router

__all__ = ["create_router"]
