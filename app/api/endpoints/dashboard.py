# app/api/endpoints/dashboard.py - YENİ YAPIYA GÖRE GÜNCELLENMİŞ

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List

from app.database import get_db
from app.models import User, AnalysisResult
from app.auth import get_current_user
from app.services.dashboard_builder import get_dashboard_builder
from app.services.recommendation_engine import RecommendationEngine
from app.services.ai.llm_service import get_llm_service
from app.schemas.dashboard import AlertItem

router = APIRouter()


# ============================================================
# 📌 AI EXECUTIVE SUMMARY
# ============================================================

@router.get("/dashboard/ai-summary")
async def get_ai_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI Executive Summary - User tablosundaki executive_summary alanını okur."""
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            return {'has_data': False, 'message': 'Kullanıcı bulunamadı.'}
        
        if user.executive_summary:
            return {
                'has_data': True,
                'executive_summary': user.executive_summary,
                'trend_summary': user.trend_summary,
                'executive_updated_at': user.executive_updated_at.isoformat() if user.executive_updated_at else None,
                'trend_updated_at': user.trend_updated_at.isoformat() if user.trend_updated_at else None,
                'full_name': user.full_name,
                'email': user.email,
                'company_name': user.company_name,
                'token_balance': user.token_balance,
            }
        else:
            return {
                'has_data': False,
                'message': 'Henüz executive summary oluşturulmamış.',
                'executive_summary': None,
                'trend_summary': None,
                'executive_updated_at': None,
            }
    except Exception as e:
        print(f"❌ AI Summary hatası: {e}")
        import traceback
        traceback.print_exc()
        return {'has_data': False, 'message': str(e)}


@router.get("/dashboard/ai-summary/status")
async def get_ai_summary_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI Summary Status - User tablosundaki executive_summary durumunu kontrol eder."""
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user or not user.executive_summary:
        return {
            'is_completed': False,
            'ai_status': 'pending',
            'message': 'Henüz executive summary oluşturulmamış.'
        }
    
    return {
        'is_completed': True,
        'ai_status': 'completed',
        'executive_updated_at': user.executive_updated_at.isoformat() if user.executive_updated_at else None
    }


# ============================================================
# 📌 DASHBOARD SUMMARY - YENİ YAPI
# ============================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard Summary - Yeni Dashboard Builder ile."""
    try:
        builder = get_dashboard_builder(db, current_user.id)
        summary = builder.build_dashboard()
        
        return {
            'success': True,
            'data': summary
        }
    except Exception as e:
        print(f"❌ Dashboard summary hatası: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'data': {
                'modules': {},
                'top_priority_module': None,
                'top_priority': 0,
                'summary': 'Özet oluşturulamadı.',
                'alerts': [],
                'updated_at': datetime.utcnow().isoformat()
            }
        }


# ============================================================
# 📌 ALERTS - YENİ YAPI
# ============================================================

@router.get("/dashboard/alerts")
async def get_dashboard_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tüm modüllerin attention'larını toplar."""
    try:
        builder = get_dashboard_builder(db, current_user.id)
        summary = builder.build_dashboard()
        
        return {
            'success': True,
            'alerts': summary.get('alerts', [])
        }
    except Exception as e:
        import traceback
        print(f"❌ Alert hatası: {e}")
        print(traceback.format_exc())
        return {
            'success': True,
            'alerts': [],
            'error': str(e)
        }


# ============================================================
# 📌 RECOMMENDATION
# ============================================================

@router.get("/dashboard/recommendation")
async def get_dashboard_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard Recommendation - En yüksek öncelikli aksiyon."""
    try:
        builder = get_dashboard_builder(db, current_user.id)
        summary = builder.build_dashboard()
        
        rec_engine = RecommendationEngine(db, current_user.id)
        recommendation = rec_engine.get_top_recommendation(summary)
        
        return {
            'success': True,
            'recommendation': recommendation,
            'dashboard_summary': summary
        }
    except Exception as e:
        print(f"❌ Recommendation hatası: {e}")
        return {
            'success': False,
            'recommendation': None,
            'dashboard_summary': {}
        }


@router.get("/dashboard/ai-recommendation")
async def get_ai_dashboard_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI Presentation - Seçilen aksiyonu açıklar."""
    try:
        builder = get_dashboard_builder(db, current_user.id)
        summary = builder.build_dashboard()
        
        rec_engine = RecommendationEngine(db, current_user.id)
        recommendation = rec_engine.get_top_recommendation(summary)
        
        if not recommendation:
            return {
                'success': True,
                'has_recommendation': False,
                'message': 'Henüz yeterli analiz verisi yok.'
            }
        
        # AI açıklaması oluştur
        llm = get_llm_service()
        
        prompt = f"""
You are a senior Supply Chain Consultant providing a brief executive recommendation.

**Selected Action:**
- Analysis: {recommendation.get('analysis', '')}
- Priority: {recommendation.get('priority', 0)}
- Title: {recommendation.get('title', '')}
- Reason: {recommendation.get('reason', '')}
- Expected Benefit: {recommendation.get('expected_benefit', '')}
- Target Page: {recommendation.get('target_page', '')}

Write a concise 2-3 sentence executive recommendation that:
1. States what should be done
2. Explains why it's important
3. Mentions the expected benefit

Keep the tone professional, clear, and actionable.
"""
        
        try:
            ai_response = llm.generate(prompt, temperature=0.3, max_tokens=200)
        except Exception as e:
            print(f"❌ AI açıklama hatası: {e}")
            ai_response = f"{recommendation.get('title', '')} öneriliyor. {recommendation.get('reason', '')}"
        
        return {
            'success': True,
            'has_recommendation': True,
            'recommendation': recommendation,
            'ai_explanation': ai_response,
            'target_page': recommendation.get('target_page', '/dashboard'),
            'analysis_id': recommendation.get('analysis_id'),
            'analysis_type': recommendation.get('analysis_type'),
            'dataset_id': recommendation.get('dataset_id'),
        }
    except Exception as e:
        print(f"❌ AI Recommendation hatası: {e}")
        return {
            'success': False,
            'has_recommendation': False,
            'message': str(e)
        }


# ============================================================
# 📌 TODAY'S DECISION
# ============================================================

@router.get("/dashboard/todays-decision")
async def get_todays_decision(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bugünün Kararı - AI Decision Engine'den gelen en güncel karar."""
    try:
        # En son analiz sonucunu al (AI Decision içeren)
        result = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == current_user.id,
            AnalysisResult.ai_status == 'decision_completed',
            AnalysisResult.data.isnot(None)
        ).order_by(AnalysisResult.created_at.desc()).first()
        
        if not result:
            return {
                'success': True,
                'has_decision': False,
                'message': 'Henüz AI kararı oluşturulmamış.'
            }
        
        data = result.data or {}
        ai_decision = data.get('ai_decision')
        
        if not ai_decision:
            return {
                'success': True,
                'has_decision': False,
                'message': 'Henüz AI kararı oluşturulmamış.'
            }
        
        return {
            'success': True,
            'has_decision': True,
            'decision': ai_decision
        }
    except Exception as e:
        print(f"❌ Bugünün kararı hatası: {e}")
        return {
            'success': False,
            'has_decision': False,
            'message': str(e)
        }


# ============================================================
# 📌 CHANGE (SON ANALİZDEN BU YANA NE DEĞİŞTİ?)
# ============================================================

@router.get("/dashboard/change")
async def get_dashboard_changes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Son Analizden Bu Yana Ne Değişti?"""
    try:
        from app.services.dashboard_change_engine import get_dashboard_change_engine
        
        engine = get_dashboard_change_engine(db, current_user.id)
        changes = engine.get_all_changes()
        gains = engine.get_gains()
        
        return {
            'success': True,
            'changes': changes,
            'gains': gains,
            'has_changes': bool(changes and any(v for v in changes.values() if v))
        }
    except Exception as e:
        import traceback
        print(f"❌ Dashboard Change hatası: {e}")
        print(traceback.format_exc())
        return {
            'success': False,
            'changes': {},
            'gains': [],
            'has_changes': False,
            'error': str(e)
        }