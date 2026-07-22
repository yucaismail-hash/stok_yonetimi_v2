# app/api/endpoints/dashboard.py - TAM VE ÇALIŞIR DOSYA

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, AnalysisResult, AnalysisDataset
from app.auth import get_current_user
from app.services.dashboard_summary_engine import get_dashboard_summary_engine
from app.services.recommendation_engine import RecommendationEngine
from app.services.ai.llm_service import get_llm_service

router = APIRouter()


# ============================================================
# 📌 MEVCUT ENDPOINT'LER (KORUNUYOR)
# ============================================================

@router.get("/dashboard/ai-summary")
async def get_ai_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI Executive Summary - Mevcut endpoint
    """
    try:
        # Son executive summary'yi al
        executive = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == current_user.id,
            AnalysisResult.result_type == 'executive_summary'
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not executive:
            return {
                'has_data': False,
                'message': 'Henüz executive summary oluşturulmamış.'
            }
        
        return {
            'has_data': True,
            'summary': executive.data.get('summary', ''),
            'executive_recommendations': executive.data.get('recommendations', []),
            'executive_updated_at': executive.created_at.isoformat(),
            'confidence': executive.data.get('confidence', 0.85),
        }
    except Exception as e:
        print(f"❌ AI Summary hatası: {e}")
        return {
            'has_data': False,
            'message': str(e)
        }


@router.get("/dashboard/ai-summary/status")
async def get_ai_summary_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI Summary Status - Mevcut endpoint
    """
    executive = db.query(AnalysisResult).filter(
        AnalysisResult.user_id == current_user.id,
        AnalysisResult.result_type == 'executive_summary'
    ).order_by(
        AnalysisResult.created_at.desc()
    ).first()
    
    if not executive:
        return {
            'is_completed': False,
            'ai_status': 'pending',
            'message': 'Henüz executive summary oluşturulmamış.'
        }
    
    return {
        'is_completed': True,
        'ai_status': 'completed',
        'executive_updated_at': executive.created_at.isoformat()
    }


# ============================================================
# 🆕 YENİ ENDPOINT'LER - DECISION ENGINE
# ============================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dashboard Summary - Tüm analiz sonuçlarının özeti.
    """
    engine = get_dashboard_summary_engine(db, current_user.id)
    summary = engine.get_dashboard_summary()
    
    return {
        'success': True,
        'data': summary
    }


@router.get("/dashboard/recommendation")
async def get_dashboard_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dashboard Recommendation - En yüksek öncelikli aksiyon.
    """
    # 1. Dashboard summary'yi al
    summary_engine = get_dashboard_summary_engine(db, current_user.id)
    dashboard_summary = summary_engine.get_dashboard_summary()
    
    # 2. Recommendation Engine ile en yüksek priority'li aksiyonu seç
    rec_engine = RecommendationEngine(db, current_user.id)
    recommendation = rec_engine.get_top_recommendation(dashboard_summary)
    
    return {
        'success': True,
        'recommendation': recommendation,
        'dashboard_summary': dashboard_summary
    }


@router.get("/dashboard/ai-recommendation")
async def get_ai_dashboard_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI Presentation - Seçilen aksiyonu açıklar.
    """
    # 1. Recommendation'ı al
    summary_engine = get_dashboard_summary_engine(db, current_user.id)
    dashboard_summary = summary_engine.get_dashboard_summary()
    
    rec_engine = RecommendationEngine(db, current_user.id)
    recommendation = rec_engine.get_top_recommendation(dashboard_summary)
    
    if not recommendation:
        return {
            'success': True,
            'has_recommendation': False,
            'message': 'Henüz yeterli analiz verisi yok.'
        }
    
    # 2. AI ile açıklama oluştur
    llm = get_llm_service()
    
    prompt = f"""
You are a senior Supply Chain Consultant providing a brief executive recommendation.

**Selected Action:**
- Analysis: {recommendation['analysis']}
- Priority: {recommendation['priority']}
- Title: {recommendation['title']}
- Reason: {recommendation['reason']}
- Expected Benefit: {recommendation['expected_benefit']}

**Dashboard Summary:**
{_format_dashboard_summary(dashboard_summary)}

**Your Task:**
Write a concise 2-3 sentence executive recommendation that:
1. States what should be done
2. Explains why it's important
3. Mentions the expected benefit

Keep the tone professional, clear, and actionable.
"""
    
    ai_response = llm.generate_text(prompt, temperature=0.3, max_tokens=150)
    
    return {
        'success': True,
        'has_recommendation': True,
        'recommendation': recommendation,
        'ai_explanation': ai_response,
        'target_page': recommendation['target_page'],
        'analysis_id': recommendation['analysis_id'],
        'analysis_type': recommendation['analysis_type'],
        'dataset_id': recommendation['dataset_id'],
    }


# ============================================================
# 📌 YARDIMCI FONKSİYONLAR
# ============================================================

def _format_dashboard_summary(summary: Dict[str, Any]) -> str:
    """Dashboard summary'i metin formatına çevir."""
    lines = []
    modules = summary.get('modules', {})
    
    for key, data in modules.items():
        if data:
            priority = data.get('priority', 0)
            if priority >= 90:
                priority_label = 'CRITICAL'
            elif priority >= 70:
                priority_label = 'HIGH'
            elif priority >= 40:
                priority_label = 'MEDIUM'
            else:
                priority_label = 'LOW'
            
            lines.append(f"- {key.upper()}: {data.get('summary', '')} (Priority: {priority} - {priority_label})")
    
    return '\n'.join(lines) if lines else 'No active analysis modules.'