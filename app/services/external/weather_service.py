# app/services/external/weather_service.py
"""
Weather Service
Fetches weather data (sector dependent).
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.services.external.base_external_service import BaseExternalService

logger = logging.getLogger(__name__)


class WeatherService(BaseExternalService):
    """
    Hava durumu servisi.
    
    Sektöre bağlı olarak hava durumu verilerini çeker.
    - Tarım sektörü için: Yağış, sıcaklık, nem
    - Turizm sektörü için: Güneşli günler, sıcaklık
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cache_ttl_hours = 12  # 12 saat
    
    async def get_weather_data(
        self,
        location: str = "Istanbul",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Hava durumu verilerini getir.
        """
        params = {
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
        }
        
        def fetch_func():
            return self._fetch_weather(location, start_date, end_date)
        
        return self.get_external_data(
            service_name="weather",
            params=params,
            fetch_func=fetch_func,
        )
    
    def _fetch_weather(
        self,
        location: str = "Istanbul",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gerçek hava durumu verisini çek.
        """
        # Mock veri
        return {
            "location": location,
            "period": {
                "start": start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end": end_date or datetime.now().strftime("%Y-%m-%d"),
            },
            "data": [
                {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), 
                 "temperature": 15 + i % 10, 
                 "rainfall": 0.5 + (i % 5) * 0.1,
                 "humidity": 60 + (i % 20)}
                for i in range(30)
            ],
            "summary": {
                "avg_temperature": 18.5,
                "total_rainfall": 45.2,
                "avg_humidity": 65.3,
            },
            "last_updated": datetime.now().isoformat(),
        }
    
    async def get_weather_impact(
        self,
        sector: str,
        start_date: str,
        end_date: str,
        location: str = "Istanbul",
    ) -> Dict[str, Any]:
        """
        Hava durumunun sektöre etkisini analiz et.
        """
        weather = await self.get_weather_data(location, start_date, end_date)
        
        impact_factor = 1.0
        
        if sector == "agriculture" or sector == "gida":
            # Tarım sektörü - Yağış ve sıcaklık
            rainfall = weather.get("summary", {}).get("total_rainfall", 0)
            if rainfall > 100:
                impact_factor = 0.8  # Çok yağmur = düşük talep
            elif rainfall < 20:
                impact_factor = 1.2  # Az yağmur = yüksek talep (sulama)
        
        elif sector == "tourism" or sector == "otel":
            # Turizm sektörü - Güneşli günler
            temp = weather.get("summary", {}).get("avg_temperature", 20)
            if temp > 25:
                impact_factor = 1.3  # Sıcak hava = yüksek talep
            elif temp < 15:
                impact_factor = 0.7  # Soğuk hava = düşük talep
        
        elif sector == "construction" or sector == "insaat":
            # İnşaat sektörü - Yağış
            rainfall = weather.get("summary", {}).get("total_rainfall", 0)
            if rainfall > 50:
                impact_factor = 0.7  # Çok yağmur = düşük talep
            elif rainfall < 10:
                impact_factor = 1.1  # Az yağmur = yüksek talep
        
        return {
            "sector": sector,
            "location": location,
            "impact_factor": impact_factor,
            "confidence": 0.75,
            "recommendation": "Adjust forecast by {:.0f}%".format((impact_factor - 1) * 100),
        }