# app/api/endpoints/dashboard.py - GÜNCELLENMİŞ

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import logging

from app.database import get_db
from app.models import User, AnalysisResult
from app.auth import get_current_user
from app.analysis.ai_summary_engine import AISummaryEngine, get_language_from_country
from app.analysis.trend_summary_engine import TrendSummaryEngine
from app.analysis.executive_summary_engine import ExecutiveSummaryEngine
from app.api.endpoints.upload import get_user_upload_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Konfigürasyon
AI_DASHBOARD_ANALYSIS_COUNT = int(os.getenv("AI_DASHBOARD_ANALYSIS_COUNT", "10"))

# Engine instance'ları
ai_engine = AISummaryEngine()


# app/api/endpoints/dashboard.py - GÜNCELLENMİŞ

@router.get("/ai-summary")
async def get_dashboard_ai_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dashboard AI yönetici özetini döndürür.
    """
    
    user_language = get_language_from_country(current_user.billing_country or "TR")
    
        # 1. Executive Summary var mı kontrol et
    if current_user.executive_summary:
        logger.info(f"✅ Executive Summary bulundu (User: {current_user.id})")
        executive = current_user.executive_summary
        
        # ✅ Önce summary alanını kontrol et, yoksa manager_summary dene
        summary_text = executive.get("summary") or executive.get("manager_summary") or "Analizleriniz başarıyla tamamlandı."
        
        return {
            "has_data": True,
            "summary": summary_text,
            "trend_direction": executive.get("trend_direction", executive.get("company_direction", "Bilinmiyor")),
            "risk_trend": executive.get("risk_trend", "Bilinmiyor"),
            "key_insights": executive.get("key_insights", executive.get("key_developments", [])),
            "recurring_issues": executive.get("recurring_issues", executive.get("recurring_problems", [])),
            "improvements": executive.get("improvements", []),
            "executive_recommendations": executive.get("executive_recommendations", []),
            "critical_attention": executive.get("critical_attention", []),
            "confidence": executive.get("confidence", 0.5),
            "executive_updated_at": current_user.executive_updated_at.isoformat() if current_user.executive_updated_at else None,
        }
    
    # 2. Executive Summary yoksa oluştur
    logger.info(f"🔄 Yeni Executive Summary oluşturuluyor (User: {current_user.id})")
    
    trend_engine = TrendSummaryEngine(language=user_language)
    exec_engine = ExecutiveSummaryEngine(language=user_language)
    
    recent_analyses = trend_engine.get_recent_analyses(db, current_user.id)
    
    if not recent_analyses:
        return {
            "has_data": False,
            "summary": None,
            "message": "Henüz yeterli analiz bulunmuyor. En az 1 analiz yapmalısınız.",
            "last_analysis_date": None
        }
    
    # Trend Summary oluştur
    trend_summary = trend_engine.build_trend_summary(recent_analyses)
    
    # Executive Summary oluştur
    executive_summary = exec_engine.build_executive_summary(
        trend_summary=trend_summary,
        previous_executive=current_user.executive_summary
    )
    
    # Kaydet
    current_user.trend_summary = trend_summary
    current_user.trend_updated_at = datetime.utcnow()
    current_user.executive_summary = executive_summary
    current_user.executive_updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"✅ Yeni Executive Summary oluşturuldu (User: {current_user.id})")
    
    return {
        "has_data": True,
        "summary": executive_summary.get("summary", ""),
        "trend_direction": executive_summary.get("trend_direction", "Bilinmiyor"),
        "risk_trend": executive_summary.get("risk_trend", "Bilinmiyor"),
        "key_insights": executive_summary.get("key_insights", []),
        "recurring_issues": executive_summary.get("recurring_issues", []),
        "improvements": executive_summary.get("improvements", []),
        "executive_recommendations": executive_summary.get("executive_recommendations", []),
        "critical_attention": executive_summary.get("critical_attention", []),
        "confidence": executive_summary.get("confidence", 0.5),
        "executive_updated_at": current_user.executive_updated_at.isoformat(),
    }

