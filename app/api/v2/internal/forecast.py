# app/api/v2/internal/forecast.py
"""
Internal Forecast API V2
Only called by Workflow Engine
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.security import EncryptionService
from app.models.dataset import Dataset
from app.analysis.forecast import DemandForecaster  # ✅ Doğru import
from app.analysis.pattern import AdvancedDemandAnalyzer

router = APIRouter()


class ForecastRequest(BaseModel):
    """Internal forecast request."""
    dataset_id: int
    user_id: int
    workflow_id: str
    params: Optional[Dict[str, Any]] = None
    previous_results: Optional[Dict[str, Any]] = None


@router.post("/")
async def forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db),
):
    """
    Internal Forecast endpoint.
    Sadece Workflow Engine tarafından çağrılır.
    """
    # 1. Dataset'i kontrol et
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.user_id == request.user_id
    ).first()
    
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    # 2. Dataset'i decrypt et
    encryption = EncryptionService(db)
    data = encryption.decrypt_dataset(request.user_id, dataset.encrypted_data)
    
    # 3. Forecast çalıştır (mevcut engine)
    pattern_analyzer = AdvancedDemandAnalyzer()
    forecaster = DemandForecaster(seasonal_periods=52)
    forecaster.set_pattern_analyzer(pattern_analyzer)
    
    # Veriyi hazırla
    items = data.get("items", [])
    if not items:
        return {
            "step": "forecast",
            "status": "failed",
            "error": "No data items found"
        }
    
    # Her SKU için forecast yap
    results = []
    for item in items:
        historical = item.get("demand_history", [])
        if not historical:
            historical = [item.get("demand", 0)]
        
        if len(historical) < 4:
            continue
        
        horizon = request.params.get("horizon", 13) if request.params else 13
        
        try:
            forecast_result = forecaster.forecast(
                historical_data=historical,
                horizon=horizon,
                model_type=request.params.get("model_type", "auto") if request.params else "auto"
            )
            
            results.append({
                "sku": item.get("sku_code", ""),
                "forecast": forecast_result.get("mean", []),
                "model_used": forecast_result.get("model_used", "simple"),
                "selection_info": forecast_result.get("selection_info", {}),
                "lower_80": forecast_result.get("lower_80", []),
                "upper_80": forecast_result.get("upper_80", []),
                "lower_95": forecast_result.get("lower_95", []),
                "upper_95": forecast_result.get("upper_95", []),
            })
        except Exception as e:
            results.append({
                "sku": item.get("sku_code", ""),
                "error": str(e)
            })
    
    return {
        "step": "forecast",
        "status": "completed",
        "result": {
            "total_items": len(results),
            "results": results
        }
    }