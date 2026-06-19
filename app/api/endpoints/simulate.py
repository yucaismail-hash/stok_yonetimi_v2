from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.simulation.monte_carlo import MonteCarloInventorySimulator

router = APIRouter()
simulator = MonteCarloInventorySimulator()

class SimulateRequest(BaseModel):
    initial_stock: float
    lead_time_mean: float
    lead_time_std: float
    demand_mean: float
    demand_std: float
    eoq: float
    rop: float
    weeks: Optional[int] = 26
    n_simulations: Optional[int] = 1000
    lead_time_dist: Optional[str] = "lognormal"
    
    # Gelişmiş modüller (seçimli)
    use_regime: Optional[bool] = False
    historical_demand: Optional[List[float]] = None
    use_copula: Optional[bool] = False
    correlation: Optional[float] = 0.7
    use_adaptive_ss: Optional[bool] = False
    target_service: Optional[float] = 0.95
    adaptive_review_period: Optional[int] = 4
    adaptive_inc_rate: Optional[float] = 0.08
    adaptive_dec_rate: Optional[float] = 0.03

@router.post("/simulate")
def run_simulation(request: SimulateRequest):
    try:
        simulator.n_simulations = request.n_simulations
        result = simulator.simulate(
            initial_stock=request.initial_stock,
            lead_time_mean=request.lead_time_mean,
            lead_time_std=request.lead_time_std,
            demand_mean=request.demand_mean,
            demand_std=request.demand_std,
            eoq=request.eoq,
            rop=request.rop,
            weeks=request.weeks,
            lead_time_dist=request.lead_time_dist,
            use_regime=request.use_regime,
            historical_demand=request.historical_demand,
            use_copula=request.use_copula,
            correlation=request.correlation,
            use_adaptive_ss=request.use_adaptive_ss,
            target_service=request.target_service,
            review_period=request.adaptive_review_period,
            inc_rate=request.adaptive_inc_rate,
            dec_rate=request.adaptive_dec_rate
        )
        # Büyük listeleri çıktıdan çıkar (sadece özet bilgiler)
        return {
            'service_level': result['service_level'],
            'cvar_95': result['cvar_95'],
            'avg_stock': result['avg_stock'][:13],  # ilk 13 hafta
            'stockout_probability': result['stockout_probability'][:13],
            'expected_shortage': result['expected_shortage'][:13],
            'regime_used': result['regime_used'],
            'copula_used': result['copula_used'],
            'adaptive_ss_used': result['adaptive_ss_used']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/simulate/info")
def get_simulation_info():
    return {
        "description": "Monte Carlo stok simülasyonu - Gelişmiş modüller seçimli",
        "advanced_modules": {
            "use_regime": "Talebi düşük/yüksek rejimlere ayırır (geçmiş veri gerekir)",
            "use_copula": "Talep ile lead time arasında korelasyon kurar",
            "use_adaptive_ss": "Simülasyon içinde ROP'u hedef servis seviyesine göre günceller"
        },
        "default_simple": "use_regime=false, use_copula=false, use_adaptive_ss=false",
        "recommended": "Orta/ileri seviye kullanıcılar için regime veya copula açılabilir"
    }