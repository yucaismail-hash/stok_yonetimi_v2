# app/api/v2/__init__.py
"""
API V2 - New architecture following DOCUMENT 01 and DOCUMENT 02
"""

from fastapi import APIRouter

from app.api.v2.endpoints import business_workflow, dataset, health, pilot_ingestion
from app.api.v2.internal import router as internal_router

router = APIRouter(prefix="/api/v2")

# External endpoints (kullanıcıya açık)
router.include_router(dataset.router, prefix="/dataset", tags=["Dataset"])
router.include_router(pilot_ingestion.router, prefix="/dataset", tags=["Dataset Pilot"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(business_workflow.router)

# Internal endpoints (sadece workflow çağırır)
router.include_router(internal_router, tags=["Internal"])
