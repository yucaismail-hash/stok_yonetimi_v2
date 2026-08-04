# app/services/security/encryption_service.py
"""
AES-256 Encryption Service
DOCUMENT 01 - Security
DOCUMENT 02 - Dataset Storage

Her şirket kendi bağımsız şifreleme anahtarına sahiptir.
Dataset'ler AES-256 ile şifrelenir.
Sadece çalıştırma sırasında memory'de decrypt edilir.
"""

import os
import base64
import hashlib
import json
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
import logging

from app.models.security import CompanyEncryptionKey
from app.models.company import User

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    AES-256 şifreleme servisi.
    Her şirket için ayrı anahtar yönetimi.
    """
    
    # Master key (environment variable'dan alınacak)
    # Bu key, tüm company key'lerini şifrelemek için kullanılır
    MASTER_KEY_ENV = "STOKONOMI_MASTER_KEY"
    
    def __init__(self, db: Session):
        self.db = db
        self.master_key = self._get_master_key()
        
    def _get_master_key(self) -> bytes:
        """Master key'i environment'dan al."""
        master_key = os.getenv(self.MASTER_KEY_ENV)
        if not master_key:
            # Development ortamında otomatik oluştur
            logger.warning(f"{self.MASTER_KEY_ENV} environment variable not set. Using development key.")
            master_key = "dev-master-key-32-bytes-long!!"  # 32 bytes
        return master_key.encode('utf-8')
    
    def _derive_key(self, salt: bytes, key_length: int = 32) -> bytes:
        """PBKDF2 ile anahtar türet."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.master_key)
    
    def _generate_salt(self) -> bytes:
        """Rastgele salt üret."""
        return os.urandom(16)
    
    def _generate_iv(self) -> bytes:
        """Rastgele IV (Initialization Vector) üret."""
        return os.urandom(16)
    
    def _encrypt_aes256(self, data: bytes, key: bytes, iv: bytes) -> bytes:
        """AES-256 CBC ile şifrele."""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # PKCS7 padding
        pad_len = 16 - (len(data) % 16)
        padded_data = data + bytes([pad_len] * pad_len)
        
        return encryptor.update(padded_data) + encryptor.finalize()
    
    def _decrypt_aes256(self, encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
        """AES-256 CBC ile çöz."""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # PKCS7 padding'i kaldır
        pad_len = decrypted[-1]
        return decrypted[:-pad_len]
    
    def _get_company_key(self, user_id: int) -> Optional[bytes]:
        """Şirketin şifreleme anahtarını al."""
        key_record = self.db.query(CompanyEncryptionKey).filter(
            CompanyEncryptionKey.user_id == user_id,
            CompanyEncryptionKey.is_active == 1
        ).first()
        
        if not key_record:
            return None
        
        # Anahtarı çöz (master key ile decrypt)
        encrypted_key = base64.b64decode(key_record.encrypted_key)
        salt = encrypted_key[:16]
        encrypted = encrypted_key[16:]
        
        derived_key = self._derive_key(salt)
        iv = encrypted[:16]
        ciphertext = encrypted[16:]
        
        decrypted_key = self._decrypt_aes256(ciphertext, derived_key, iv)
        
        return decrypted_key
    
    def _create_company_key(self, user_id: int) -> bytes:
        """Yeni şirket şifreleme anahtarı oluştur."""
        # 32 byte AES-256 anahtar
        company_key = os.urandom(32)
        
        # Anahtarı master key ile şifrele
        salt = self._generate_salt()
        derived_key = self._derive_key(salt)
        iv = self._generate_iv()
        
        encrypted_key = self._encrypt_aes256(company_key, derived_key, iv)
        
        # Salt + IV + Encrypted Key
        combined = salt + iv + encrypted_key
        encoded = base64.b64encode(combined).decode('utf-8')
        
        # Veritabanına kaydet
        key_record = CompanyEncryptionKey(
            user_id=user_id,
            encrypted_key=encoded,
            key_version="1"
        )
        self.db.add(key_record)
        self.db.commit()
        
        logger.info(f"✅ Company encryption key created for user_id: {user_id}")
        
        return company_key
    
    def get_or_create_company_key(self, user_id: int) -> bytes:
        """Şirket anahtarını al, yoksa oluştur."""
        key = self._get_company_key(user_id)
        if key:
            return key
        
        return self._create_company_key(user_id)
    
    def encrypt_dataset(self, user_id: int, data: Dict[str, Any]) -> str:
        """
        Dataset'i şifrele.
        DOCUMENT 02 - Section 15: Dataset Storage
        """
        # JSON'ı string'e çevir
        json_data = json.dumps(data, ensure_ascii=False)
        data_bytes = json_data.encode('utf-8')
        
        # Şirket anahtarını al
        company_key = self.get_or_create_company_key(user_id)
        
        # Rastgele IV üret
        iv = self._generate_iv()
        
        # Şifrele
        encrypted = self._encrypt_aes256(data_bytes, company_key, iv)
        
        # IV + Encrypted Data
        combined = iv + encrypted
        encoded = base64.b64encode(combined).decode('utf-8')
        
        # Anahtar kullanım zamanını güncelle
        key_record = self.db.query(CompanyEncryptionKey).filter(
            CompanyEncryptionKey.user_id == user_id,
            CompanyEncryptionKey.is_active == 1
        ).first()
        if key_record:
            key_record.last_used_at = func.now()
            self.db.commit()
        
        return encoded
    
    def decrypt_dataset(self, user_id: int, encrypted_data: str) -> Dict[str, Any]:
        """
        Dataset'i çöz.
        Sadece memory'de decrypt edilir.
        """
        # Base64 decode
        combined = base64.b64decode(encrypted_data)
        
        # IV ve ciphertext'i ayır
        iv = combined[:16]
        ciphertext = combined[16:]
        
        # Şirket anahtarını al
        company_key = self.get_or_create_company_key(user_id)
        
        # Çöz
        decrypted_bytes = self._decrypt_aes256(ciphertext, company_key, iv)
        
        # JSON'a çevir
        json_data = decrypted_bytes.decode('utf-8')
        data = json.loads(json_data)
        
        # Anahtar kullanım zamanını güncelle
        key_record = self.db.query(CompanyEncryptionKey).filter(
            CompanyEncryptionKey.user_id == user_id,
            CompanyEncryptionKey.is_active == 1
        ).first()
        if key_record:
            key_record.last_used_at = func.now()
            self.db.commit()
        
        return data
    
    def rotate_company_key(self, user_id: int) -> bool:
        """
        Şirket şifreleme anahtarını yenile.
        Eski anahtar pasifleştirilir, yeni anahtar oluşturulur.
        """
        # Eski anahtarı pasifleştir
        old_key = self.db.query(CompanyEncryptionKey).filter(
            CompanyEncryptionKey.user_id == user_id,
            CompanyEncryptionKey.is_active == 1
        ).first()
        
        if old_key:
            old_key.is_active = 0
        
        # Yeni anahtar oluştur
        self._create_company_key(user_id)
        
        logger.info(f"✅ Company encryption key rotated for user_id: {user_id}")
        
        return True
    
    def get_key_status(self, user_id: int) -> Dict[str, Any]:
        """Şirket anahtarının durumunu getir."""
        key_record = self.db.query(CompanyEncryptionKey).filter(
            CompanyEncryptionKey.user_id == user_id
        ).order_by(CompanyEncryptionKey.id.desc()).first()
        
        if not key_record:
            return {
                "exists": False,
                "active": False,
                "key_version": None,
                "created_at": None,
                "last_used_at": None
            }
        
        return {
            "exists": True,
            "active": key_record.is_active == 1,
            "key_version": key_record.key_version,
            "created_at": key_record.created_at,
            "last_used_at": key_record.last_used_at
        }


class DatasetEncryptionMixin:
    """
    Dataset model'i için encryption mixin.
    SQLAlchemy model'ine kolayca eklenebilir.
    """
    
    def encrypt_data(self, encryption_service: EncryptionService, user_id: int):
        """Dataset verisini şifrele."""
        if hasattr(self, '_decrypted_data'):
            data = self._decrypted_data
            self.encrypted_data = encryption_service.encrypt_dataset(user_id, data)
    
    def decrypt_data(self, encryption_service: EncryptionService, user_id: int) -> Dict[str, Any]:
        """Dataset verisini çöz."""
        if not self.encrypted_data:
            return {}
        
        data = encryption_service.decrypt_dataset(user_id, self.encrypted_data)
        self._decrypted_data = data
        return data