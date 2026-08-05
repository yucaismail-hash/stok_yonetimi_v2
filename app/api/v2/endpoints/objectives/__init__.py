# app/api/v2/endpoints/objectives/__init__.py
"""Objectives endpoints - Business capability execution."""
from app.api.v2.endpoints.objectives.run import router

__all__ = ["router"]