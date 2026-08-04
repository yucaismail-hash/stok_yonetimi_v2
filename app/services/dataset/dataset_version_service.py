# app/services/dataset/dataset_version_service.py
"""
Dataset Version Service
DOCUMENT 02 - Section 7: Dataset Versioning
"""

from typing import Optional, Dict, Any, List
import hashlib
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.dataset import Dataset, DatasetVersion, DatasetEvent

logger = logging.getLogger(__name__)


class DatasetVersionService:
    """Dataset versiyon yönetimi."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_version(self, dataset_id: int, user_id: int) -> DatasetVersion:
        """Yeni dataset versiyonu oluştur."""
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Mevcut en son versiyonu bul
        last_version = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id
        ).order_by(desc(DatasetVersion.version_number)).first()
        
        next_version = (last_version.version_number + 1) if last_version else 1
        
        # Yeni versiyon oluştur
        version = DatasetVersion(
            dataset_id=dataset_id,
            version_number=next_version,
            dataset_hash=dataset.dataset_hash,
            record_count=dataset.record_count,
            sku_count=dataset.sku_count,
            created_by=user_id,
            previous_version_id=last_version.id if last_version else None,
            is_current=True,
            is_archived=False,
        )
        
        # Eski versiyonu pasifleştir
        if last_version:
            last_version.is_current = False
            self.db.add(last_version)
        
        self.db.add(version)
        
        # Dataset'teki versiyon numarasını güncelle
        dataset.dataset_version = next_version
        self.db.add(dataset)
        
        self.db.commit()
        
        logger.info(f"✅ Dataset {dataset_id} version {next_version} created")
        
        return version
    
    def get_version(self, dataset_id: int, version_number: Optional[int] = None) -> Optional[DatasetVersion]:
        """Versiyon bilgisini getir."""
        query = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id
        )
        
        if version_number:
            query = query.filter(DatasetVersion.version_number == version_number)
        else:
            query = query.filter(DatasetVersion.is_current == True)
        
        return query.first()
    
    def get_all_versions(self, dataset_id: int) -> List[DatasetVersion]:
        """Dataset'in tüm versiyonlarını getir."""
        return self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id
        ).order_by(DatasetVersion.version_number.desc()).all()
    
    def archive_version(self, version_id: int) -> bool:
        """Versiyonu arşivle."""
        version = self.db.query(DatasetVersion).filter(
            DatasetVersion.id == version_id
        ).first()
        
        if not version:
            return False
        
        version.is_archived = True
        self.db.commit()
        
        logger.info(f"✅ Version {version_id} archived")
        
        return True
    
    def log_event(self, dataset_id: int, event_type: str, user_id: int, event_data: Optional[Dict] = None):
        """Dataset olayını logla."""
        event = DatasetEvent(
            dataset_id=dataset_id,
            event_type=event_type,
            event_data=event_data,
            created_by=user_id,
        )
        
        self.db.add(event)
        self.db.commit()
        
        logger.info(f"📝 Dataset {dataset_id} event: {event_type}")
        
        return event