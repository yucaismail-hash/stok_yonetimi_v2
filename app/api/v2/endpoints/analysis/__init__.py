# app/api/v2/endpoints/analysis/__init__.py
"""Analysis endpoints - Single analysis execution."""
from app.api.v2.endpoints.analysis.run import router

__all__ = ["router"]