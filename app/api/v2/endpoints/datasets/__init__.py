# app/api/v2/endpoints/datasets/__init__.py
"""Dataset endpoints - CRUD operations."""
from app.api.v2.endpoints.datasets.create import router as create_router
from app.api.v2.endpoints.datasets.retrieve import router as retrieve_router
from app.api.v2.endpoints.datasets.validate import router as validate_router
from app.api.v2.endpoints.datasets.approve import router as approve_router

__all__ = ["create_router", "retrieve_router", "validate_router", "approve_router"]