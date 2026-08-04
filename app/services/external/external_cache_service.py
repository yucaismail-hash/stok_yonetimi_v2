# app/services/external/external_cache_service.py
"""
External Cache Service
Caches external data downloads.
DOCUMENT 01 - Downloaded external datasets MUST be cached.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.models.external import ExternalCache

logger = logging.getLogger(__name__)


class ExternalCacheService:
    """
    External Data Cache Servisi.
    
    Dış veriler cache'lenir:
    - Enflasyon verileri
    - Döviz kurları
    - Hava durumu
    - Tatil günleri
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Cache'den veri getir."""
        cache = self.db.query(ExternalCache).filter(
            ExternalCache.cache_key == cache_key,
            ExternalCache.is_valid == True,
            ExternalCache.expires_at > datetime.now()
        ).first()
        
        if cache:
            cache.hit_count += 1
            cache.last_accessed_at = datetime.now()
            self.db.commit()
            return {
                "data": cache.cached_data,
                "cached_at": cache.created_at,
                "expires_at": cache.expires_at,
            }
        
        return None
    
    def set(
        self,
        cache_key: str,
        data: Dict[str, Any],
        service_name: str,
        ttl_hours: int = 24,
    ) -> ExternalCache:
        """Veriyi cache'e kaydet."""
        # Eski cache'i geçersiz kıl
        self.invalidate(cache_key)
        
        # Yeni cache oluştur
        cache = ExternalCache(
            cache_key=cache_key,
            service_name=service_name,
            cached_data=data,
            data_hash=self._calculate_hash(data),
            expires_at=datetime.now() + timedelta(hours=ttl_hours),
            is_valid=True,
            hit_count=0,
        )
        
        self.db.add(cache)
        self.db.commit()
        self.db.refresh(cache)
        
        logger.info(f"✅ Cache set: {service_name} - {cache_key}")
        
        return cache
    
    def invalidate(self, cache_key: str):
        """Cache'i geçersiz kıl."""
        cache = self.db.query(ExternalCache).filter(
            ExternalCache.cache_key == cache_key,
            ExternalCache.is_valid == True
        ).first()
        
        if cache:
            cache.is_valid = False
            self.db.commit()
            logger.info(f"✅ Cache invalidated: {cache_key}")
    
    def cleanup_expired(self) -> int:
        """Süresi dolmuş cache'leri temizle."""
        count = self.db.query(ExternalCache).filter(
            ExternalCache.expires_at <= datetime.now()
        ).delete()
        self.db.commit()
        
        if count > 0:
            logger.info(f"🧹 Cleaned up {count} expired external caches")
        
        return count
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Veri hash'i hesapla."""
        import hashlib
        import json
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]