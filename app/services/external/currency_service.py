# app/services/external/currency_service.py
"""
Currency Service
Fetches exchange rate data.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.services.external.base_external_service import BaseExternalService

logger = logging.getLogger(__name__)


class CurrencyService(BaseExternalService):
    """
    Döviz kuru servisi.
    
    Merkez Bankası veya diğer kaynaklardan döviz kurlarını çeker.
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cache_ttl_hours = 6  # 6 saat
    
    async def get_exchange_rates(
        self,
        base_currency: str = "USD",
        target_currencies: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Döviz kurlarını getir.
        """
        params = {
            "base": base_currency,
            "targets": target_currencies or ["TRY", "EUR", "GBP"],
        }
        
        def fetch_func():
            return self._fetch_exchange_rates(base_currency, target_currencies)
        
        return self.get_external_data(
            service_name="currency",
            params=params,
            fetch_func=fetch_func,
        )
    
    def _fetch_exchange_rates(
        self,
        base_currency: str = "USD",
        target_currencies: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Gerçek döviz verisini çek.
        """
        # Mock veri
        targets = target_currencies or ["TRY", "EUR", "GBP"]
        rates = {}
        
        for target in targets:
            if target == "TRY":
                rates[target] = 42.5
            elif target == "EUR":
                rates[target] = 0.92
            elif target == "GBP":
                rates[target] = 0.79
            else:
                rates[target] = 1.0
        
        return {
            "base": base_currency,
            "rates": rates,
            "last_updated": datetime.now().isoformat(),
            "source": "tcmb",
        }