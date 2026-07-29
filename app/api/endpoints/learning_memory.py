# app/api/endpoints/learning_memory.py
# Company Learning Memory Endpoint'leri

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.services.learning_engine import LearningEngine
from app.services.learning_score_service import LearningScoreService

router = APIRouter()


@router.get("/learning/memory")
async def get_company_memory(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Şirket hafızasındaki tüm öğrenilmiş kuralları getirir.
    """
    try:
        engine = LearningEngine(db, current_user.id)
        rules = engine.get_company_memory(limit)
        
        return {
            'success': True,
            'total': len(rules),
            'rules': rules
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/learning/memory/verified")
async def get_verified_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sadece doğrulanmış kuralları getirir.
    """
    try:
        engine = LearningEngine(db, current_user.id)
        rules = engine.get_verified_rules()
        
        return {
            'success': True,
            'total': len(rules),
            'rules': rules
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/learning/score")
async def get_learning_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Şirket öğrenme seviyesini hesaplar.
    """
    try:
        service = LearningScoreService(db, current_user.id)
        score = service.calculate_learning_score()
        
        return {
            'success': True,
            'data': score
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/learning/analyze")
async def trigger_learning_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Belirli bir analiz sonucunu Learning Engine ile işler.
    """
    try:
        from app.models import AnalysisResult
        
        # Analiz sonucunu al
        result = db.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id,
            AnalysisResult.user_id == current_user.id
        ).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Analiz sonucu bulunamadı")
        
        # Learning Engine'i çalıştır
        engine = LearningEngine(db, current_user.id)
        learning_result = engine.analyze_and_learn({
            'result_type': result.result_type,
            'data': result.data
        })
        
        return {
            'success': True,
            'learning_result': learning_result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))