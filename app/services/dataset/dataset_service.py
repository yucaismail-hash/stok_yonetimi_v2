# app/services/dataset/dataset_service.py
"""
Dataset Service
Main service for dataset operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import json
import logging

from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetState, DatasetOperationType
from app.models.company import User
from app.services.security import EncryptionService

logger = logging.getLogger(__name__)


class DatasetService:
    """
    Dataset Service - Ana dataset işlemleri.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_dataset(
        self,
        user_id: int,
        data: Dict[str, Any],
        source_type: str,
        source_name: Optional[str] = None,
        operation_type: str = "append",
    ) -> Dataset:
        """
        Yeni dataset oluştur.
        """
        # Dataset hash hesapla
        dataset_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        # SKU ve record sayıları
        items = data.get("items", [])
        skus = set(item.get("sku_code") for item in items if item.get("sku_code"))
        sku_count = len(skus)
        record_count = len(items)
        
        # Tarih aralığı
        weeks = [item.get("week_start") for item in items if item.get("week_start")]
        date_range_start = min(weeks) if weeks else None
        date_range_end = max(weeks) if weeks else None
        
        # Dataset oluştur
        dataset = Dataset(
            user_id=user_id,
            dataset_hash=dataset_hash,
            dataset_version=1,
            source_type=source_type,
            source_name=source_name,
            state=DatasetState.UPLOADED,
            operation_type=DatasetOperationType(operation_type),
            uploaded_by=user_id,
            upload_timestamp=datetime.now(),
            record_count=record_count,
            sku_count=sku_count,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            is_active=True,
        )
        
        # Şifrele
        encryption = EncryptionService(self.db)
        encrypted_data = encryption.encrypt_dataset(user_id, data)
        dataset.encrypted_data = encrypted_data
        
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        
        logger.info(f"✅ Dataset created: {dataset.id} for user {user_id}")
        
        return dataset
    
    def get_dataset(self, dataset_id: int, user_id: int) -> Optional[Dataset]:
        """Dataset getir."""
        return self.db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
            Dataset.is_active == True
        ).first()
    
    def get_dataset_with_data(self, dataset_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Dataset'i verisiyle birlikte getir."""
        dataset = self.get_dataset(dataset_id, user_id)
        if not dataset:
            return None
        
        encryption = EncryptionService(self.db)
        data = encryption.decrypt_dataset(user_id, dataset.encrypted_data)
        
        return {
            "dataset": dataset,
            "data": data
        }
    
    def list_datasets(
        self,
        user_id: int,
        state: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Dataset listesi getir."""
        query = self.db.query(Dataset).filter(
            Dataset.user_id == user_id,
            Dataset.is_active == True
        )
        
        if state:
            query = query.filter(Dataset.state == state)
        
        total = query.count()
        datasets = query.order_by(Dataset.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": datasets
        }
    
    def update_state(
        self,
        dataset_id: int,
        user_id: int,
        new_state: str,
    ) -> Optional[Dataset]:
        """Dataset durumunu güncelle."""
        dataset = self.get_dataset(dataset_id, user_id)
        if not dataset:
            return None
        
        dataset.state = DatasetState(new_state)
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        
        logger.info(f"✅ Dataset {dataset_id} state updated to: {new_state}")
        
        return dataset
    
    def delete_dataset(self, dataset_id: int, user_id: int) -> bool:
        """Dataset'i sil (soft delete)."""
        dataset = self.get_dataset(dataset_id, user_id)
        if not dataset:
            return False
        
        dataset.is_active = False
        self.db.add(dataset)
        self.db.commit()
        
        logger.info(f"✅ Dataset {dataset_id} deleted")
        
        return True