# app/services/external/base_external_service.py
"""
Base External Service
Common functionality for all external data sources.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json
import hashlib

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseExternalService:
    """
    External Service Base Class.
    
    Tüm external servisler bu sınıftan türetilir.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl_hours = 24  # Varsayılan cache süresi
    
    def _generate_cache_key(self, service_name: str, params: Dict[str, Any]) -> str:
        """Cache key üret."""
        data = f"{service_name}_{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _should_refresh_cache(self, cached_at: datetime) -> bool:
        """Cache yenilenmeli mi kontrol et."""
        if not cached_at:
            return True
        age = datetime.now() - cached_at
        return age > timedelta(hours=self.cache_ttl_hours)
    
    def get_external_data(
        self,
        service_name: str,
        params: Dict[str, Any],
        fetch_func,
    ) -> Dict[str, Any]:
        """
        External veriyi getir.
        Cache kontrolü yapar.
        """
        cache_key = self._generate_cache_key(service_name, params)
        
        # Cache'den kontrol et
        from app.services.external.external_cache_service import ExternalCacheService
        cache_service = ExternalCacheService(self.db)
        
        cached = cache_service.get(cache_key)
        
        if cached and not self._should_refresh_cache(cached.get("cached_at")):
            logger.info(f"✅ Cache hit: {service_name} - {cache_key}")
            return cached.get("data", {})
        
        # Fetch yap
        try:
            logger.info(f"📡 Fetching external data: {service_name}")
            data = fetch_func()
            
            # Cache'e kaydet
            cache_service.set(
                cache_key=cache_key,
                data=data,
                service_name=service_name,
                ttl_hours=self.cache_ttl_hours,
            )
            
            return data
            
        except Exception as e:
            logger.error(f"❌ External fetch failed: {service_name} - {str(e)}")
            
            # Eski cache varsa döndür (stale data)
            if cached:
                logger.warning(f"⚠️ Returning stale cache for {service_name}")
                return cached.get("data", {})
            
            raise