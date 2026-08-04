# app/services/external/holiday_service.py
"""
Holiday Service
Fetches holiday and calendar data.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.services.external.base_external_service import BaseExternalService

logger = logging.getLogger(__name__)


class HolidayService(BaseExternalService):
    """
    Tatil günleri servisi.
    
    Resmi tatilleri, dini bayramları, özel günleri çeker.
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cache_ttl_hours = 720  # 30 gün
    
    async def get_holidays(
        self,
        year: int,
        country: str = "TR",
    ) -> Dict[str, Any]:
        """
        Tatil günlerini getir.
        """
        params = {"year": year, "country": country}
        
        def fetch_func():
            return self._fetch_holidays(year, country)
        
        return self.get_external_data(
            service_name="holidays",
            params=params,
            fetch_func=fetch_func,
        )
    
    def _fetch_holidays(self, year: int, country: str = "TR") -> Dict[str, Any]:
        """
        Gerçek tatil verisini çek.
        """
        # Mock veri - 2026 Türkiye tatilleri
        return {
            "country": country,
            "year": year,
            "holidays": [
                {"date": f"{year}-01-01", "name": "Yılbaşı", "type": "national"},
                {"date": f"{year}-04-23", "name": "Ulusal Egemenlik ve Çocuk Bayramı", "type": "national"},
                {"date": f"{year}-05-01", "name": "Emek ve Dayanışma Günü", "type": "national"},
                {"date": f"{year}-05-19", "name": "Atatürk'ü Anma, Gençlik ve Spor Bayramı", "type": "national"},
                {"date": f"{year}-07-15", "name": "Demokrasi ve Milli Birlik Günü", "type": "national"},
                {"date": f"{year}-08-30", "name": "Zafer Bayramı", "type": "national"},
                {"date": f"{year}-10-29", "name": "Cumhuriyet Bayramı", "type": "national"},
                # Dini bayramlar (yaklaşık)
                {"date": f"{year}-03-20", "name": "Ramazan Bayramı", "type": "religious"},
                {"date": f"{year}-03-21", "name": "Ramazan Bayramı", "type": "religious"},
                {"date": f"{year}-03-22", "name": "Ramazan Bayramı", "type": "religious"},
                {"date": f"{year}-05-27", "name": "Kurban Bayramı", "type": "religious"},
                {"date": f"{year}-05-28", "name": "Kurban Bayramı", "type": "religious"},
                {"date": f"{year}-05-29", "name": "Kurban Bayramı", "type": "religious"},
                {"date": f"{year}-05-30", "name": "Kurban Bayramı", "type": "religious"},
            ],
            "last_updated": datetime.now().isoformat(),
        }
    
    async def is_holiday(self, date: str, country: str = "TR") -> bool:
        """
        Belirtilen tarih tatil mi kontrol et.
        """
        year = int(date[:4])
        holidays = await self.get_holidays(year, country)
        
        for holiday in holidays.get("holidays", []):
            if holiday.get("date") == date:
                return True
        
        return False
    
    async def get_holiday_impact(
        self,
        start_date: str,
        end_date: str,
        country: str = "TR",
    ) -> Dict[str, Any]:
        """
        Belirtilen periyottaki tatillerin etkisini analiz et.
        """
        # Tarihleri parse et
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        holidays = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            if await self.is_holiday(date_str, country):
                holidays.append(date_str)
            current += timedelta(days=1)
        
        return {
            "period": {
                "start": start_date,
                "end": end_date,
            },
            "holiday_count": len(holidays),
            "holidays": holidays,
            "impact_score": len(holidays) * 2,  # Her tatil günü deman 2x etki
        }