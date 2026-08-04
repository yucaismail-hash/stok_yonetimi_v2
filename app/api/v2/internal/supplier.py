# app/api/v2/internal/supplier.py
"""
Internal Supplier API V2
Only called by Workflow Engine
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.security import EncryptionService
from app.models.dataset import Dataset
from app.analysis.supplier import SupplierPerformanceAnalyzer, SupplierShareOptimizer

router = APIRouter()


class SupplierRequest(BaseModel):
    dataset_id: int
    user_id: int
    workflow_id: str
    params: Optional[Dict[str, Any]] = None
    previous_results: Optional[Dict[str, Any]] = None


@router.post("/")
async def supplier(
    request: SupplierRequest,
    db: Session = Depends(get_db),
):
    """
    Internal Supplier endpoint.
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
    
    analyzer = SupplierPerformanceAnalyzer()
    optimizer = SupplierShareOptimizer(analyzer)
    
    # Supplier verilerini çıkar
    suppliers_data = data.get("suppliers", {})
    supplier_mapping = data.get("supplier_mapping", {})
    
    results = []
    
    for supplier_id, supplier_info in suppliers_data.items():
        try:
            risk_score = analyzer.get_supplier_risk_score(supplier_id)
            performance_score = analyzer.get_supplier_performance_score(supplier_id)
            
            results.append({
                "supplier_id": supplier_id,
                "name": supplier_info.get("name", supplier_id),
                "risk_score": risk_score,
                "performance_score": performance_score,
                "lead_time_mean": supplier_info.get("lt_mean", 14),
                "lead_time_std": supplier_info.get("lt_std", 3),
                "ontime_rate": supplier_info.get("ontime_rate", 0.8),
            })
        except Exception as e:
            results.append({
                "supplier_id": supplier_id,
                "error": str(e)
            })
    
    return {
        "step": "supplier",
        "status": "completed",
        "result": {
            "total_items": len(results),
            "suppliers": results
        }
    }