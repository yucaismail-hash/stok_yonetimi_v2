# app/api/v2/endpoints/health.py
"""
Health Check Endpoint
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """
    System health check.
    """
    try:
        # Database check
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as exc:
        # Render must not accept a database-unavailable API as ready.  Keep
        # credentials and connection details out of the public response.
        logger.warning("health_database_unavailable", extra={"error_class": type(exc).__name__})
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "version": "v2",
                "database": "unavailable",
                "message": "Database readiness is unavailable",
            },
        )
    
    return {
        "status": "ok",
        "version": "v2",
        "database": db_status,
        "message": "Stokonomi AI API V2 is running"
    }
