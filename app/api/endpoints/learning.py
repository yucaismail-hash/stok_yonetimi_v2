from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.analysis.historical_learning import HistoricalLearningSystem
from app.auth import get_current_user
from app.models import User

router = APIRouter()
historical_learning = HistoricalLearningSystem()

class HistoricalLearnRequest(BaseModel):
    material_code: str
    group: str
    weekly_data: List[float]
    lead_time_days: int
    service_level: Optional[float] = 0.95


@router.post("/historical-learn")
def historical_learn(request: HistoricalLearnRequest, current_user: User = Depends(get_current_user)):
    """
    Kayan pencere yöntemi ile tarihsel öğrenme
    8 hafta eğitim, 4 hafta test
    """
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