# app/api/v2/internal/safety_stock.py
"""
Internal Safety Stock API V2
Only called by Workflow Engine
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.security import EncryptionService
from app.models.dataset import Dataset
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer

router = APIRouter()


class SafetyStockRequest(BaseModel):
    dataset_id: int
    user_id: int
    workflow_id: str
    params: Optional[Dict[str, Any]] = None
    previous_results: Optional[Dict[str, Any]] = None


@router.post("/")
async def safety_stock(
    request: SafetyStockRequest,
    db: Session = Depends(get_db),
):
    """
    Internal Safety Stock endpoint.
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
    
    # Forecast sonucunu al (previous_results'tan)
    forecast_result = request.previous_results.get("forecast", {}) if request.previous_results else {}
    
    optimizer = ComprehensiveSafetyStockOptimizer()
    
    items = data.get("items", [])
    results = []
    
    service_level = request.params.get("service_level", 0.95) if request.params else 0.95
    
    for item in items:
        historical = item.get("demand_history", [])
        if not historical:
            historical = [item.get("demand", 0)]
        
        if len(historical) < 4:
            continue
        
        lead_time = item.get("lead_time_days", 14)
        
        try:
            ss_result = optimizer.calculate_all_methods(
                weekly_data=historical,
                lead_time_days=lead_time,
                service_level=service_level
            )
            
            results.append({
                "sku": item.get("sku_code", ""),
                "safety_stock": ss_result.get("hybrid_ss", 0),
                "classic_ss": ss_result.get("classic_ss", 0),
                "croston_ss": ss_result.get("croston_ss", 0),
                "syntetos_boylan_ss": ss_result.get("syntetos_boylan_ss", 0),
                "bootstrapping_ss": ss_result.get("bootstrapping_ss", 0),
                "ml_ss": ss_result.get("ml_ss", 0),
            })
        except Exception as e:
            results.append({
                "sku": item.get("sku_code", ""),
                "error": str(e)
            })
    
    return {
        "step": "safety_stock",
        "status": "completed",
        "result": {
            "total_items": len(results),
            "results": results
        }
    }