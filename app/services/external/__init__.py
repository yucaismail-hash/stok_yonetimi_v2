# app/services/external/__init__.py
"""
External Intelligence Services
DOCUMENT 01 - External Intelligence

Collects verified external information:
- Inflation
- Currency
- Interest rate
- Holidays
- Calendar
- Housing index
- Google Trends
- Weather (sector dependent)
"""

from app.services.external.base_external_service import BaseExternalService
from app.services.external.inflation_service import InflationService
from app.services.external.currency_service import CurrencyService
from app.services.external.holiday_service import HolidayService
from app.services.external.weather_service import WeatherService
from app.services.external.trends_service import TrendsService
from app.services.external.external_cache_service import ExternalCacheService

__all__ = [
    "BaseExternalService",
    "InflationService",
    "CurrencyService",
    "HolidayService",
    "WeatherService",
    "TrendsService",
    "ExternalCacheService",
]