# app/api/endpoints/dashboard.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List

from app.database import get_db
from app.models import User, AnalysisResult
from app.auth import get_current_user
from app.services.dashboard_summary_engine import get_dashboard_summary_engine, DashboardSummaryEngine
from app.services.recommendation_engine import RecommendationEngine
from app.services.ai.llm_service import get_llm_service
from app.schemas.dashboard import AlertItem

router = APIRouter()


# ============================================================
# 📌 AI EXECUTIVE SUMMARY - User tablosundan okur (DÜZELTİLDİ)
# ============================================================

@router.get("/dashboard/ai-summary")
async def get_ai_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI Executive Summary - User tablosundaki executive_summary alanını okur.
    """
    try:
        # ✅ DOĞRU: User tablosundan oku
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            return {
                'has_data': False,
                'message': 'Kullanıcı bulunamadı.'
            }
        
        # ✅ executive_summary alanını kontrol et
        if user.executive_summary:
            return {
                'has_data': True,
                'executive_summary': user.executive_summary,  # ✅ Ana veri
                'trend_summary': user.trend_summary,
                'executive_updated_at': user.executive_updated_at.isoformat() if user.executive_updated_at else None,
                'trend_updated_at': user.trend_updated_at.isoformat() if user.trend_updated_at else None,
                # User bilgileri de gönder (frontend'de kullanmak için)
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
        return {
            'has_data': False,
            'message': str(e)
        }


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
# 📌 DECISION ENGINE ENDPOINT'LERİ
# ============================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard Summary - Tüm analiz sonuçlarının özeti."""
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
    """Dashboard Recommendation - En yüksek öncelikli aksiyon."""
    summary_engine = get_dashboard_summary_engine(db, current_user.id)
    dashboard_summary = summary_engine.get_dashboard_summary()
    
    rec_engine = RecommendationEngine(db, current_user.id)
    recommendation = rec_engine.get_top_recommendation(dashboard_summary)
    
    return {
        'success': True,
        'recommendation': recommendation,
        'dashboard_summary': dashboard_summary
    }

# app/api/endpoints/dashboard.py - get_ai_dashboard_recommendation (DÜZELTİLMİŞ)

@router.get("/dashboard/ai-recommendation")
async def get_ai_dashboard_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI Presentation - Seçilen aksiyonu açıklar.
    """
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
    
    # ✅ AI açıklaması oluştur
    llm = get_llm_service()
    
    # ✅ Prompt'u zenginleştir
    prompt = f"""
You are a senior Supply Chain Consultant providing a brief executive recommendation.

**Selected Action:**
- Analysis: {recommendation['analysis']}
- Priority: {recommendation['priority']} ({recommendation.get('priority_label', '')})
- Title: {recommendation['title']}
- Reason: {recommendation['reason']}
- Expected Benefit: {recommendation['expected_benefit']}
- Target Page: {recommendation['target_page']}

**Dashboard Summary:**
{_format_dashboard_summary(dashboard_summary)}

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
        ai_response = f"{recommendation['title']} öneriliyor. {recommendation['reason']}"
    
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
# 🆕 /alerts ENDPOINT'İ
# ============================================================

@router.get("/dashboard/alerts")
async def get_dashboard_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tüm modüllerin attention'larını toplar."""
    try:
        engine = DashboardSummaryEngine(db, current_user.id)
        alerts = engine.get_all_alerts()
        
        # alerts zaten dict listesi ise direkt döndür
        if alerts and isinstance(alerts[0], dict):
            return {
                'success': True,
                'alerts': alerts
            }
        
        # AlertItem nesnesi ise dict'e çevir
        alert_items = []
        for alert in alerts:
            if hasattr(alert, 'dict'):
                alert_items.append(alert.dict())
            elif hasattr(alert, '__dict__'):
                alert_items.append({
                    'id': getattr(alert, 'id', ''),
                    'severity': getattr(alert, 'severity', 'info'),
                    'title': getattr(alert, 'title', ''),
                    'description': getattr(alert, 'description', ''),
                    'action_label': getattr(alert, 'action_label', 'İncele →'),
                    'action_path': getattr(alert, 'action_path', '/dashboard'),
                    'priority': getattr(alert, 'priority', 0)
                })
            else:
                alert_items.append(alert)
        
        return {
            'success': True,
            'alerts': alert_items
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
# 📌 YARDIMCI FONKSİYONLAR
# ============================================================

def _format_dashboard_summary(summary: Dict[str, Any]) -> str:
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

# app/api/endpoints/dashboard.py - /dashboard/change endpoint'i (DÜZELTİLMİŞ)

@router.get("/dashboard/change")
async def get_dashboard_changes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Son Analizden Bu Yana Ne Değişti?
    """
    try:
        from app.services.dashboard_change_engine import get_dashboard_change_engine
        
        engine = get_dashboard_change_engine(db, current_user.id)
        changes = engine.get_all_changes()
        gains = engine.get_gains()
        
        # ✅ DEBUG: Logla
        print(f"🔍 Changes: {changes}")
        print(f"🔍 Gains: {gains}")
        
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

    
