from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.analysis.backtest import BacktestEngine

router = APIRouter()
backtest_engine = BacktestEngine()

class BacktestRequest(BaseModel):
    historical_demand: List[float]
    lead_time_days: int = 14
    holding_cost_rate: Optional[float] = 0.20
    shortage_cost: Optional[float] = 500.0
    unit_cost: Optional[float] = 100.0
    test_window: Optional[int] = 26
    strategies: Optional[List[str]] = None

@router.post("/backtest")
def run_backtest(request: BacktestRequest):
    """
    Geçmiş talep verisi üzerinde farklı emniyet stoğu stratejilerini test eder.
    
    - **historical_demand**: En az 52 haftalık veri önerilir (son test_window hafta test olur)
    - **test_window**: Kaç hafta test edileceği (varsayılan: 26 hafta)
    - **strategies**: Test edilecek stratejiler (None = hepsi)
    
    Strateji listesi: ai, classic, croston, syntetos_boylan, ml, hybrid, simple_moving_avg, last_value
    
    Metrikler:
    - service_level: Talep karşılama oranı
    - total_cost: Toplam maliyet (holding + shortage)
    - stockout_probability: Stok tükenme olasılığı (hafta bazında)
    """
    try:
        result = backtest_engine.run_backtest(
            historical_demand=request.historical_demand,
            lead_time_days=request.lead_time_days,
            holding_cost_rate=request.holding_cost_rate,
            shortage_cost=request.shortage_cost,
            unit_cost=request.unit_cost,
            test_window=request.test_window,
            strategies=request.strategies
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/backtest/info")
def get_backtest_info():
    return {
        "description": "Geçmiş veri üzerinde strateji karşılaştırması (backtest)",
        "strategies": {
            "ai": "AI hibrit (pattern multiplier dahil)",
            "classic": "Klasik normal dağılım formülü",
            "croston": "Croston metodu (aralıklı talep için)",
            "syntetos_boylan": "Syntetos-Boylan (Croston'ın iyileştirilmişi)",
            "ml": "Makine öğrenmesi özellik tabanlı",
            "hybrid": "Tüm metodların ağırlıklı ortalaması",
            "simple_moving_avg": "Basit hareketli ortalama",
            "last_value": "Son değer (naif tahmin)"
        },
        "metrikler": [
            "service_level (0-1, 1 en iyi)",
            "total_cost (TL, düşük iyi)",
            "stockout_probability (0-1, 0 en iyi)",
            "total_shortage (birim)",
            "avg_inventory (birim)"
        ],
        "kullanım": "En düşük maliyetli stratejiyi bulmak için kullanılır."
    }