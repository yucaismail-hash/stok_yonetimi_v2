# app/services/external/trends_service.py
"""
Google Trends Service
Fetches Google Trends data.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.services.external.base_external_service import BaseExternalService

logger = logging.getLogger(__name__)


class TrendsService(BaseExternalService):
    """
    Google Trends servisi.
    
    DOCUMENT 01: Google Trends
    Arama trendlerini çeker.
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cache_ttl_hours = 168  # 7 gün
    
    async def get_trends(
        self,
        keywords: List[str],
        region: str = "TR",
        period: str = "30d",
    ) -> Dict[str, Any]:
        """
        Google Trends verilerini getir.
        """
        params = {
            "keywords": keywords,
            "region": region,
            "period": period,
        }
        
        def fetch_func():
            return self._fetch_trends(keywords, region, period)
        
        return self.get_external_data(
            service_name="trends",
            params=params,
            fetch_func=fetch_func,
        )
    
    def _fetch_trends(
        self,
        keywords: List[str],
        region: str = "TR",
        period: str = "30d",
    ) -> Dict[str, Any]:
        """
        Gerçek Google Trends verisini çek.
        """
        # Mock veri
        return {
            "keywords": keywords,
            "region": region,
            "period": period,
            "data": [
                {
                    "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                    **{kw: 50 + (i % 20) + (kw == "gıda" and i % 2 == 0) * 10
                       for kw in keywords}
                }
                for i in range(30)
            ],
            "summary": {
                "trending": keywords[0] if keywords else None,
                "momentum": "up" if len(keywords) > 1 else "stable",
            },
            "last_updated": datetime.now().isoformat(),
        }
    
    async def get_trend_impact(
        self,
        keywords: List[str],
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Trendlerin talep üzerindeki etkisini analiz et.
        """
        trends = await self.get_trends(keywords, period=f"{days}d")
        
        # Trend momentumunu hesapla
        data = trends.get("data", [])
        if not data:
            return {"impact_factor": 1.0, "confidence": 0.0}
        
        # Son 7 gün vs önceki 7 gün
        last_7 = data[:7]
        prev_7 = data[7:14] if len(data) > 14 else data[:7]
        
        avg_last = sum(sum(item.get(kw, 0) for kw in keywords) for item in last_7) / len(last_7)
        avg_prev = sum(sum(item.get(kw, 0) for kw in keywords) for item in prev_7) / len(prev_7)
        
        if avg_prev > 0:
            change = (avg_last - avg_prev) / avg_prev
            impact_factor = 1.0 + (change * 0.5)  # %50 etki
            impact_factor = max(0.7, min(1.3, impact_factor))
        else:
            impact_factor = 1.0
        
        return {
            "keywords": keywords,
            "impact_factor": impact_factor,
            "trend_change": change if avg_prev > 0 else 0,
            "confidence": 0.6,
            "recommendation": (
                "Increase forecast" if impact_factor > 1.05 else
                "Decrease forecast" if impact_factor < 0.95 else
                "No adjustment needed"
            ),
        }