# app/api/v2/endpoints/artifacts/__init__.py
"""AI Artifact endpoints - Retrieval and management."""
from app.api.v2.endpoints.artifacts.by_execution import router as by_execution_router

__all__ = [
    "by_execution_router",
]
