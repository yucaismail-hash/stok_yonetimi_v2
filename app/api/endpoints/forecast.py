# Önce eski placeholder'ı silip yeniden oluşturalım
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.analysis.forecast import DemandForecaster

router = APIRouter()
forecaster = DemandForecaster()

class ForecastRequest(BaseModel):
    historical_data: List[float]
    horizon: int = 13
    model_type: Optional[str] = "auto"  # auto, holt_winters, arima, simple

class ForecastResponse(BaseModel):
    mean: List[float]
    lower_80: List[float]
    upper_80: List[float]
    lower_95: List[float]
    upper_95: List[float]

@router.post("/forecast", response_model=ForecastResponse)
def get_forecast(request: ForecastRequest):
    """
    Talep tahmini yapar.
    
    - **historical_data**: Geçmiş haftalık talep verileri (en az 4 hafta)
    - **horizon**: Tahmin edilecek hafta sayısı (varsayılan: 13)
    - **model_type**: 
        - "auto": Otomatik seçim (önerilen)
        - "holt_winters": Mevsimsel model (52+ hafta veri gerekir)
        - "arima": ARIMA modeli
        - "simple": Basit ağırlıklı ortalama + trend
    """
    try:
        result = forecaster.forecast(
            request.historical_data,
            horizon=request.horizon,
            model_type=request.model_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/forecast/info")
def get_forecast_info():
    """Forecast modülü hakkında bilgi verir."""
    return {
        "available_models": ["auto", "holt_winters", "arima", "simple"],
        "requirements": {
            "holt_winters": "En az 104 hafta (2 yıl) veri önerilir",
            "arima": "En az 26 hafta veri önerilir",
            "simple": "En az 8 hafta veri gerekir"
        },
        "auto_selection": "Veri uzunluğuna göre en uygun model otomatik seçilir",
        "output": "Tahmin ortalaması + %80 ve %95 güven aralıkları"
    }