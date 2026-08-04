# app/api/v2/internal/backtest.py
"""
Internal Backtest API V2
Only called by Workflow Engine
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.security import EncryptionService
from app.models.dataset import Dataset
from app.analysis.backtest import BacktestEngine

router = APIRouter()


class BacktestRequest(BaseModel):
    dataset_id: int
    user_id: int
    workflow_id: str
    params: Optional[Dict[str, Any]] = None
    previous_results: Optional[Dict[str, Any]] = None


@router.post("/")
async def backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
):
    """
    Internal Backtest endpoint.
    Sadece Workflow Engine tarafından çağrılır.
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.user_id == request.user_id
    ).first()
    
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    encryption = EncryptionService(db)
    data = encryption.decrypt_dataset(request.user_id, dataset.encrypted_data)
    
    # Forecast sonucunu al
    forecast_result = request.previous_results.get("forecast", {}) if request.previous_results else {}
    
    backtest_engine = BacktestEngine()
    
    items = data.get("items", [])
    results = []
    
    test_window = request.params.get("test_window", 8) if request.params else 8
    strategies = request.params.get("strategies", None) if request.params else None
    
    for item in items:
        historical = item.get("demand_history", [])
        if not historical:
            historical = [item.get("demand", 0)]
        
        if len(historical) < 8:
            continue
        
        lead_time = item.get("lead_time_days", 14)
        
        try:
            backtest_result = backtest_engine.run_backtest(
                historical_demand=historical,
                lead_time_days=lead_time,
                holding_cost_rate=0.20,
                shortage_cost=500,
                unit_cost=100,
                test_window=test_window,
                strategies=strategies
            )
            
            if "error" in backtest_result:
                results.append({
                    "sku": item.get("sku_code", ""),
                    "error": backtest_result["error"]
                })
                continue
            
            comparison = backtest_result.get("comparison", {})
            recommendation = backtest_result.get("recommendation", {})
            
            results.append({
                "sku": item.get("sku_code", ""),
                "best_strategy": recommendation.get("best_strategy", "hybrid"),
                "service_level": comparison.get("service_level", {}).get(recommendation.get("best_strategy", "hybrid"), 0),
                "total_cost": comparison.get("total_cost", {}).get(recommendation.get("best_strategy", "hybrid"), 0),
                "comparison": comparison,
            })
        except Exception as e:
            results.append({
                "sku": item.get("sku_code", ""),
                "error": str(e)
            })
    
    return {
        "step": "backtest",
        "status": "completed",
        "result": {
            "total_items": len(results),
            "results": results
        }
    }