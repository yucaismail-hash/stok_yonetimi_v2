# app/services/dataset/dataset_cache_service.py
"""
Dataset Cache Service
DOCUMENT 02 - Section 19: Incremental Analysis
DOCUMENT 02 - Section 20: Cache Invalidation
"""

from typing import Optional, Dict, Any, List
import hashlib
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.execution import ExecutionCache

logger = logging.getLogger(__name__)


class DatasetCacheService:
    """
    Dataset Cache Servisi.
    
    Incremental Analysis için:
    - Sadece değişen SKU'lar yeniden işlenir
    - Değişmeyen SKU'lar cache'den gelir
    """
    
    DEFAULT_CACHE_DURATION_DAYS = 30
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_cached_result(self, dataset_id: int, sku_code: str, result_type: str) -> Optional[Dict[str, Any]]:
        """Cache'den sonuç al."""
        cache = self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id,
            ExecutionCache.sku_code == sku_code,
            ExecutionCache.result_type == result_type,
            ExecutionCache.is_valid == True,
            ExecutionCache.expires_at > datetime.now()
        ).first()
        
        if cache:
            logger.debug(f"✅ Cache hit: {sku_code} - {result_type}")
            return cache.result_data
        
        logger.debug(f"❌ Cache miss: {sku_code} - {result_type}")
        return None
    
    def set_cached_result(
        self,
        dataset_id: int,
        sku_code: str,
        result_type: str,
        result_data: Dict[str, Any],
        algorithm_version: str,
        expire_days: int = DEFAULT_CACHE_DURATION_DAYS
    ) -> ExecutionCache:
        """Sonucu cache'e kaydet."""
        # Result hash'i hesapla
        result_hash = hashlib.sha256(
            json.dumps(result_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Eski cache'i geçersiz kıl
        self.invalidate_cache(dataset_id, sku_code, result_type)
        
        # Yeni cache oluştur
        cache = ExecutionCache(
            dataset_id=dataset_id,
            sku_code=sku_code,
            result_type=result_type,
            result_data=result_data,
            result_hash=result_hash,
            algorithm_version=algorithm_version,
            expires_at=datetime.now() + timedelta(days=expire_days),
            is_valid=True,
        )
        
        self.db.add(cache)
        self.db.commit()
        
        logger.debug(f"✅ Cache set: {sku_code} - {result_type}")
        
        return cache
    
    def invalidate_cache(self, dataset_id: int, sku_code: Optional[str] = None, result_type: Optional[str] = None):
        """Cache'i geçersiz kıl."""
        query = self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id,
            ExecutionCache.is_valid == True
        )
        
        if sku_code:
            query = query.filter(ExecutionCache.sku_code == sku_code)
        
        if result_type:
            query = query.filter(ExecutionCache.result_type == result_type)
        
        # Geçersiz kıl
        cache_entries = query.all()
        for cache in cache_entries:
            cache.is_valid = False
        
        if cache_entries:
            self.db.commit()
            logger.debug(f"✅ Cache invalidated: {len(cache_entries)} entries")
    
    def invalidate_all_by_algorithm(self, dataset_id: int, algorithm_version: str):
        """Algoritma versiyonu değiştiğinde tüm cache'i geçersiz kıl."""
        cache_entries = self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id,
            ExecutionCache.algorithm_version != algorithm_version,
            ExecutionCache.is_valid == True
        ).all()
        
        for cache in cache_entries:
            cache.is_valid = False
        
        if cache_entries:
            self.db.commit()
            logger.info(f"✅ Cache invalidated by algorithm version: {len(cache_entries)} entries")
    
    def get_cache_stats(self, dataset_id: int) -> Dict[str, Any]:
        """Cache istatistiklerini getir."""
        total = self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id
        ).count()
        
        valid = self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id,
            ExecutionCache.is_valid == True,
            ExecutionCache.expires_at > datetime.now()
        ).count()
        
        expired = self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id,
            ExecutionCache.is_valid == True,
            ExecutionCache.expires_at <= datetime.now()
        ).count()
        
        return {
            "total_cache_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "hit_rate": round((valid / total * 100) if total > 0 else 0, 2),
        }
    
    def cleanup_expired(self, dataset_id: Optional[int] = None) -> int:
        """Süresi dolmuş cache'leri temizle."""
        query = self.db.query(ExecutionCache).filter(
            ExecutionCache.expires_at <= datetime.now()
        )
        
        if dataset_id:
            query = query.filter(ExecutionCache.dataset_id == dataset_id)
        
        count = query.delete()
        self.db.commit()
        
        if count > 0:
            logger.info(f"🧹 Cleaned up {count} expired cache entries")
        
        return count