# app/services/security/key_management.py
"""
Company Encryption Key Management
"""

import os
import secrets
from typing import Optional
from sqlalchemy.orm import Session
import logging

from app.models.security import CompanyEncryptionKey
from app.services.security.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class KeyManagementService:
    """
    Şirket şifreleme anahtarlarını yönetir.
    - Anahtar oluşturma
    - Anahtar rotasyonu
    - Anahtar iptali
    - Anahtar durumu
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = EncryptionService(db)
    
    def create_key(self, user_id: int, force: bool = False) -> bool:
        """Yeni şifreleme anahtarı oluştur."""
        if not force:
            # Mevcut aktif anahtar var mı kontrol et
            existing = self.db.query(CompanyEncryptionKey).filter(
                CompanyEncryptionKey.user_id == user_id,
                CompanyEncryptionKey.is_active == 1
            ).first()
            
            if existing:
                logger.warning(f"Active key already exists for user_id: {user_id}")
                return False
        
        self.encryption_service.get_or_create_company_key(user_id)
        return True
    
    def rotate_key(self, user_id: int) -> bool:
        """Anahtarı yenile."""
        return self.encryption_service.rotate_company_key(user_id)
    
    def revoke_key(self, user_id: int) -> bool:
        """Anahtarı iptal et."""
        key_record = self.db.query(CompanyEncryptionKey).filter(
            CompanyEncryptionKey.user_id == user_id,
            CompanyEncryptionKey.is_active == 1
        ).first()
        
        if key_record:
            key_record.is_active = 0
            self.db.commit()
            logger.info(f"✅ Key revoked for user_id: {user_id}")
            return True
        
        logger.warning(f"No active key found for user_id: {user_id}")
        return False
    
    def get_key_info(self, user_id: int) -> dict:
        """Anahtar bilgisini getir."""
        return self.encryption_service.get_key_status(user_id)
    
    def reencrypt_all_datasets(self, user_id: int) -> int:
        """
        Tüm dataset'leri yeni anahtarla yeniden şifrele.
        Anahtar rotasyonu sonrası kullanılır.
        """
        from app.models.dataset import Dataset
        
        # Eski anahtarla şifrelenmiş tüm dataset'leri bul
        datasets = self.db.query(Dataset).filter(
            Dataset.user_id == user_id,
            Dataset.encrypted_data.isnot(None)
        ).all()
        
        count = 0
        for dataset in datasets:
            try:
                # Eski veriyi çöz
                data = dataset.decrypt_data(self.encryption_service, user_id)
                
                # Yeni anahtarla şifrele
                dataset.encrypt_data(self.encryption_service, user_id)
                
                count += 1
            except Exception as e:
                logger.error(f"Failed to reencrypt dataset {dataset.id}: {e}")
        
        self.db.commit()
        logger.info(f"✅ Reencrypted {count} datasets for user_id: {user_id}")
        
        return count