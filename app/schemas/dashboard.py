# app/schemas/dashboard.py
"""
Dashboard Summary Sözleşmesi - Tüm analiz modülleri bu yapıyı üretmek zorundadır.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DashboardSummary(BaseModel):
    """
    Her analiz modülünün üretmek zorunda olduğu özet yapısı.
    Bu sözleşme sayesinde Dashboard hiçbir modülün iç mantığını bilmez.
    """
    priority: int                     # 0-100 arası
    summary: str                      # Kısa özet (1-2 cümle)
    attention: List[str] = []         # Uyarı mesajları
    business_value: str               # İş değeri / beklenen fayda
    analysis_id: int
    dataset_id: Optional[int] = None
    target_page: str
    analysis_type: str
    last_run: str
    status: str = "success"
    
    # 🆕 Metrikler (her modül kendi metriklerini ekleyebilir)
    metrics: Dict[str, Any] = {}
    
    # 🆕 Kritik veriler (Attention Required için)
    critical_items: List[Dict[str, Any]] = []
    high_risk_count: int = 0
    critical_count: int = 0
    trend_up: int = 0
    trend_down: int = 0
    avg_service_level: float = 0


class DashboardSummaryResponse(BaseModel):
    modules: Dict[str, Optional[DashboardSummary]]
    top_priority_module: Optional[str]
    top_priority: int
    summary: str
    updated_at: str


class AlertItem(BaseModel):
    id: str
    severity: str  # critical, warning, info
    title: str
    description: str
    action_label: str
    action_path: str
    priority: int = 0