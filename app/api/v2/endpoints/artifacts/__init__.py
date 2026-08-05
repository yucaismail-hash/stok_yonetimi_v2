# app/api/v2/endpoints/artifacts/__init__.py
"""AI Artifact endpoints - Retrieval and management."""
from app.api.v2.endpoints.artifacts.retrieve import router as retrieve_router
from app.api.v2.endpoints.artifacts.explainability import router as explainability_router
from app.api.v2.endpoints.artifacts.versions import router as versions_router
from app.api.v2.endpoints.artifacts.by_execution import router as by_execution_router
from app.api.v2.endpoints.artifacts.by_company import router as by_company_router

__all__ = [
    "retrieve_router",
    "explainability_router",
    "versions_router",
    "by_execution_router",
    "by_company_router",
]