from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer

router = APIRouter()
optimizer = ComprehensiveSafetyStockOptimizer()

class SafetyStockRequest(BaseModel):
    weekly_data: List[float]
    lead_time_days: int = 14
    service_level: float = 0.95
    n_bootstrap_iterations: Optional[int] = 2000  # Bootstrap için iterasyon sayısı

class SafetyStockResponse(BaseModel):
    classic_ss: float
    croston_ss: float
    syntetos_boylan_ss: float
    bootstrapping_ss: float
    ml_ss: float
    hybrid_ss: float

@router.post("/safety-stock", response_model=SafetyStockResponse)
def calculate_safety_stock(request: SafetyStockRequest):
    """
    Tüm emniyet stoğu hesaplama metodlarını çalıştırır.
    
    - **classic_ss**: Klasik normal dağılım formülü
    - **croston_ss**: Kesikli/aralıklı talep için Croston metodu
    - **syntetos_boylan_ss**: Croston'ın bias düzeltilmiş versiyonu
    - **bootstrapping_ss**: Bootstrap simülasyonu ile
    - **ml_ss**: Makine öğrenmesi özellik tabanlı
    - **hybrid_ss**: Tüm metodların ağırlıklı ortalaması
    """
    try:
        # Önce feature'ları hesapla (opsiyonel, şimdilik doğrudan çağırıyoruz)
        result = optimizer.calculate_all_methods(
            request.weekly_data,
            request.lead_time_days,
            request.service_level
        )
        
        # Bootstrap için özel iterasyon sayısını kullan (isteğe bağlı)
        if request.n_bootstrap_iterations != 2000:
            bootstrapping_ss = optimizer.bootstrapping_method(
                request.weekly_data,
                request.lead_time_days,
                request.service_level,
                n_iterations=request.n_bootstrap_iterations
            )
            result['bootstrapping_ss'] = round(bootstrapping_ss, 2)
            # Hybrid'i yeniden hesapla (çünkü bootstrap değişti)
            result['hybrid_ss'] = round(optimizer.hybrid_safety_stock(
                request.weekly_data, request.lead_time_days, request.service_level
            ), 2)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/safety-stock/info")
def get_method_info():
    """Tüm SS metodları hakkında bilgi verir."""
    return {
        "methods": [
            {"name": "classic_ss", "description": "Klasik normal dağılım formülü. Sürekli talep için idealdir.", "best_for": "CV < 0.5, zero_ratio < 0.3"},
            {"name": "croston_ss", "description": "Croston metodu. Aralıklı/kesikli talep için geliştirilmiştir.", "best_for": "0.5 < zero_ratio < 0.875"},
            {"name": "syntetos_boylan_ss", "description": "Syntetos-Boylan metodu. Croston'un bias sorununu düzeltir.", "best_for": "zero_ratio > 0.5, daha az bias"},
            {"name": "bootstrapping_ss", "description": "Bootstrap simülasyonu. Dağılım varsayımı gerektirmez.", "best_for": "Her tür talep, ama hesaplama yoğun"},
            {"name": "ml_ss", "description": "Makine öğrenmesi özellik tabanlı (CV, zero_ratio, trend).", "best_for": "Karmaşık talep desenleri"},
            {"name": "hybrid_ss", "description": "Tüm metodların ağırlıklı ortalaması. Zero_ratio'ya göre ağırlıklar değişir.", "best_for": "Genel amaçlı, risk dağıtımı"}
        ],
        "default_params": {
            "lead_time_days": 14,
            "service_level": 0.95,
            "n_bootstrap_iterations": 2000
        }
    }