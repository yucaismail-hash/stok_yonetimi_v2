# app/api/v2/__init__.py
"""
API V2 - New architecture following DOCUMENT 01 and DOCUMENT 02
"""

from fastapi import APIRouter

from app.api.v2.endpoints import dataset, decision, health
from app.api.v2.internal import router as internal_router

router = APIRouter(prefix="/api/v2")

# External endpoints (kullanıcıya açık)
router.include_router(dataset.router, prefix="/dataset", tags=["Dataset"])
router.include_router(decision.router, prefix="/decision", tags=["Decision"])
router.include_router(health.router, prefix="/health", tags=["Health"])

# Internal endpoints (sadece workflow çağırır)
router.include_router(internal_router, tags=["Internal"])