# app/api/v2/internal/simulation.py
"""
Internal Simulation API V2
Only called by Workflow Engine
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.security import EncryptionService
from app.models.dataset import Dataset
from app.simulation.monte_carlo import MonteCarloInventorySimulator

router = APIRouter()


class SimulationRequest(BaseModel):
    dataset_id: int
    user_id: int
    workflow_id: str
    params: Optional[Dict[str, Any]] = None
    previous_results: Optional[Dict[str, Any]] = None


@router.post("/")
async def simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Internal Simulation endpoint.
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
    
    # Safety Stock sonucunu al
    safety_stock_result = request.previous_results.get("safety_stock", {}) if request.previous_results else {}
    
    simulator = MonteCarloInventorySimulator()
    
    items = data.get("items", [])
    results = []
    
    n_simulations = request.params.get("n_simulations", 500) if request.params else 500
    weeks = request.params.get("weeks", 26) if request.params else 26
    
    for item in items:
        historical = item.get("demand_history", [])
        if not historical:
            historical = [item.get("demand", 0)]
        
        if len(historical) < 4:
            continue
        
        lead_time = item.get("lead_time_days", 14)
        initial_stock = item.get("current_stock", 0)
        eoq = item.get("eoq", 100)
        avg_demand = sum(historical) / len(historical) if historical else 0
        demand_std = max(1, avg_demand * 0.3)
        rop = int(avg_demand * (lead_time / 7) + avg_demand * 0.3)
        
        try:
            sim_result = simulator.simulate(
                initial_stock=initial_stock,
                lead_time_mean=lead_time,
                lead_time_std=max(1, lead_time * 0.2),
                demand_mean=avg_demand,
                demand_std=demand_std,
                eoq=eoq,
                rop=rop,
                weeks=weeks,
                lead_time_dist='lognormal',
                use_regime=request.params.get("use_regime", False) if request.params else False,
                historical_demand=historical if len(historical) >= 12 else None,
                use_copula=request.params.get("use_copula", False) if request.params else False,
                use_adaptive_ss=request.params.get("use_adaptive_ss", False) if request.params else False,
            )
            
            results.append({
                "sku": item.get("sku_code", ""),
                "service_level": sim_result.get("service_level", 0),
                "cvar_95": sim_result.get("cvar_95", 0),
                "stockout_probability": sum(sim_result.get("stockout_probability", [])) / len(sim_result.get("stockout_probability", [1])) if sim_result.get("stockout_probability") else 0,
                "regime_used": sim_result.get("regime_used", False),
                "copula_used": sim_result.get("copula_used", False),
                "adaptive_ss_used": sim_result.get("adaptive_ss_used", False),
            })
        except Exception as e:
            results.append({
                "sku": item.get("sku_code", ""),
                "error": str(e)
            })
    
    return {
        "step": "simulation",
        "status": "completed",
        "result": {
            "total_items": len(results),
            "results": results
        }
    }