# app/api/v2/endpoints/health.py
"""
Health Check Endpoint
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """
    System health check.
    """
    try:
        # Database check
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "version": "v2",
        "database": db_status,
        "message": "Stokonomi AI API V2 is running"
    }