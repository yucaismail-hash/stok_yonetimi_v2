from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional, Any  # ✅ EKLENDİ
from app.analysis.historical_learning import HistoricalLearningSystem
from app.auth import get_current_user
from app.models import *
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime  # ✅ EKLENDİ

router = APIRouter()
historical_learning = HistoricalLearningSystem()


# ============================================================
# 📌 GÜNCELLENMİŞ update_learning_from_pattern (ÇİFT KATMANLI)
# ============================================================

def update_learning_from_pattern(user_id: int, results: List[Dict], db: Session):
    """
    Pattern analizi sonuçlarından öğrenme verilerini güncelle.
    ÇİFT KATMANLI: Grup bazlı + Malzeme bazlı (özetten)
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        sector_id = user.sector_id or 32
        
        # 📊 1. KATMAN: Grup Bazlı Öğrenme (TOPLU)
        group_patterns = {}
        for result in results:
            group = result.get('group', 'GENEL')
            pattern = result.get('pattern', 'DEGISKEN')
            cv = result.get('cv', 0)
            
            # CV'ye göre multiplier hesapla
            if cv > 0.7:
                multiplier = 1.3
            elif cv > 0.4:
                multiplier = 1.15
            else:
                multiplier = 1.0
            
            key = f"{group}_{pattern}"
            
            if key not in group_patterns:
                group_patterns[key] = {
                    'group': group,
                    'pattern': pattern,
                    'multiplier': multiplier,
                    'count': 1
                }
            else:
                existing = group_patterns[key]
                total = existing['count'] + 1
                existing['multiplier'] = (existing['multiplier'] * existing['count'] + multiplier) / total
                existing['count'] = total
        
        # Grup bazlı learning_key'leri kaydet
        for key, data in group_patterns.items():
            group_key = f"{user_id}_{sector_id}_{data['group']}_{data['pattern']}"
            
            existing = db.query(UserLearningData).filter(
                UserLearningData.learning_key == group_key
            ).first()
            
            if existing:
                total_samples = existing.sample_count + data['count']
                existing.pattern_multiplier = (
                    (existing.pattern_multiplier * existing.sample_count + 
                     data['multiplier'] * data['count']) / total_samples
                )
                existing.sample_count = total_samples
                existing.confidence = min(1.0, total_samples / 50)
                existing.pattern = data['pattern']
                existing.learning_type = "group"
                existing.updated_at = datetime.utcnow()
            else:
                new_learning = UserLearningData(
                    user_id=user_id,
                    sector_id=sector_id,
                    learning_key=group_key,
                    pattern_multiplier=data['multiplier'],
                    seasonal_multiplier=1.0,
                    confidence=min(1.0, data['count'] / 50),
                    sample_count=data['count'],
                    pattern=data['pattern'],
                    learning_type="group"
                )
                db.add(new_learning)
        
        db.commit()
        print(f"✅ Öğrenme verileri güncellendi: {len(group_patterns)} grup")
        
    except Exception as e:
        print(f"❌ Öğrenme güncelleme hatası: {e}")
        db.rollback()

# ============================================================
# 📌 MEVCUT ENDPOINT'LER
# ============================================================

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