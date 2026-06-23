from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.historical_learning import HistoricalLearningSystem
from app.auth import get_current_user
from app.models import User, UserLearningData
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
historical_learning = HistoricalLearningSystem()


def update_learning_from_pattern(user_id: int, results: List[Dict], db: Session):
    """Pattern analizi sonuçlarından öğrenme verilerini güncelle"""
    try:
        # Kullanıcının sektörünü al
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        sector_id = user.sector_id
        
        for result in results:
            group = result.get('group', 'GENEL')
            pattern = result.get('pattern', 'DEGISKEN')
            cv = result.get('cv', 0)
            
            # Pattern multiplier hesapla
            if cv > 0.7:
                multiplier = 1.3
            elif cv > 0.4:
                multiplier = 1.15
            else:
                multiplier = 1.0
            
            learning_key = f"{user_id}_{sector_id}_{group}_{pattern}"
            
            existing = db.query(UserLearningData).filter(
                UserLearningData.learning_key == learning_key
            ).first()
            
            if existing:
                total_samples = existing.sample_count + 1
                existing.pattern_multiplier = (
                    (existing.pattern_multiplier * existing.sample_count + multiplier) / total_samples
                )
                existing.sample_count = total_samples
                existing.confidence = min(1.0, total_samples / 50)
            else:
                new_learning = UserLearningData(
                    user_id=user_id,
                    learning_key=learning_key,
                    pattern_multiplier=multiplier,
                    seasonal_multiplier=1.0,
                    confidence=0.02,
                    sample_count=1,
                    pattern=pattern,
                    sector_id=sector_id
                )
                db.add(new_learning)
        
        db.commit()
    except Exception as e:
        print(f"Öğrenme güncelleme hatası: {e}")


class HistoricalLearnRequest(BaseModel):
    material_code: str
    group: str
    weekly_data: List[float]
    lead_time_days: int
    service_level: Optional[float] = 0.95


@router.post("/historical-learn")
def historical_learn(request: HistoricalLearnRequest, current_user: User = Depends(get_current_user)):
    """Kayan pencere yöntemi ile tarihsel öğrenme"""
    try:
        result = historical_learning.learn_from_material(
            material_code=request.material_code,
            group=request.group,
            weekly_data=request.weekly_data,
            lead_time_days=request.lead_time_days,
            service_level=request.service_level
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/historical-learning/stats")
def get_historical_stats():
    """Tarihsel öğrenme istatistiklerini getir"""
    return historical_learning.get_learning_stats()


@router.get("/historical-learning/material/{material_code}")
def get_material_learning(material_code: str):
    """Belirli bir malzemenin öğrenme geçmişini getir"""
    result = historical_learning.get_material_learning(material_code)
    if not result:
        raise HTTPException(status_code=404, detail="Malzeme bulunamadı")
    return result