# app/services/active_dataset.py
"""
Active Dataset Service - Aktif dataset'i merkezi olarak yönetir.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import AnalysisDataset

logger = logging.getLogger(__name__)


class ActiveDatasetService:
    """
    Active Dataset Servisi - Tüm uygulama için tek kaynak.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_dataset(self, user_id: int) -> Optional[AnalysisDataset]:
        """
        Kullanıcının aktif dataset'ini getirir.
        """
        return self.db.query(AnalysisDataset).filter(
            AnalysisDataset.user_id == user_id,
            AnalysisDataset.is_active == True
        ).first()
    
    def get_active_dataset_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının aktif dataset'inin dataset_data alanını getirir.
        """
        dataset = self.get_active_dataset(user_id)
        if dataset:
            return dataset.dataset_data
        return None
    
    def get_active_materials(self, user_id: int) -> list:
        """
        Aktif dataset'ten materials listesini getirir.
        """
        data = self.get_active_dataset_data(user_id)
        if data:
            return data.get('materials', [])
        return []
    


    def get_active_suppliers(self, user_id: int) -> dict:
        """
        Aktif dataset'ten suppliers dict'ini getirir.
        """
        data = self.get_active_dataset_data(user_id)
        if data:
            suppliers = data.get('suppliers', {})
            print(f"🔍 get_active_suppliers: {len(suppliers)} tedarikçi")
            if suppliers:
                print(f"   suppliers keys: {list(suppliers.keys())}")
            return suppliers
        return {}
    
    def get_active_supplier_mapping(self, user_id: int) -> dict:
        """
        Aktif dataset'ten supplier_mapping dict'ini getirir.
        """
        data = self.get_active_dataset_data(user_id)
        if data:
            supplier_mapping = data.get('supplier_mapping', {})
            print(f"🔍 get_active_supplier_mapping: {len(supplier_mapping)} ürün")
            if supplier_mapping:
                first_key = next(iter(supplier_mapping.keys()))
                print(f"   supplier_mapping keys: {list(supplier_mapping.keys())[:5]}...")
                print(f"   ilk ürün: {first_key} -> {supplier_mapping.get(first_key)}")
            return supplier_mapping
        return {}
    
    def get_active_week_columns(self, user_id: int) -> list:
        """
        Aktif dataset'ten week_columns listesini getirir.
        """
        data = self.get_active_dataset_data(user_id)
        if data:
            return data.get('week_columns', [])
        return []
    
    def get_active_upload_id(self, user_id: int) -> Optional[str]:
        """
        Aktif dataset'in upload_id'sini getirir.
        """
        dataset = self.get_active_dataset(user_id)
        if dataset:
            return dataset.upload_id
        return None
    
    def set_active_dataset(self, user_id: int, dataset_id: int) -> bool:
        """
        Belirtilen dataset'i aktif yapar, diğerlerini pasifleştirir.
        """
        try:
            # Tüm dataset'leri pasifleştir
            self.db.query(AnalysisDataset).filter(
                AnalysisDataset.user_id == user_id,
                AnalysisDataset.is_active == True
            ).update({"is_active": False})
            
            # Belirtilen dataset'i aktif yap
            self.db.query(AnalysisDataset).filter(
                AnalysisDataset.id == dataset_id,
                AnalysisDataset.user_id == user_id
            ).update({"is_active": True})
            
            self.db.commit()
            logger.info(f"✅ Active dataset updated: User {user_id}, Dataset {dataset_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Active dataset update failed: {e}")
            return False
    
# app/services/active_dataset.py - get_active_dataset_data ve get_dataset_stats

    def get_dataset_stats(self, user_id: int) -> dict:
        """
        Aktif dataset istatistiklerini getirir.
        """
        dataset = self.get_active_dataset(user_id)
        if not dataset:
            return {
                'has_data': False,
                'product_count': 0,
                'period_count': 0,
                'data_points': 0,
                'source_type': None,
                'source_name': None,
                'created_at': None,
                'week_count': 0
            }
        
        data = dataset.dataset_data or {}
        
        # ============================================================
        # ✅ DEBUG: dataset_data içeriğini logla
        # ============================================================
        print(f"🔍 Active Dataset {dataset.id} - dataset_data keys: {list(data.keys())}")
        print(f"   materials: {type(data.get('materials'))} - {len(data.get('materials', []))} satır")
        print(f"   suppliers: {type(data.get('suppliers'))} - {len(data.get('suppliers', {}))} tedarikçi")
        print(f"   supplier_mapping: {type(data.get('supplier_mapping'))} - {len(data.get('supplier_mapping', {}))} ürün")
        print(f"   week_columns: {type(data.get('week_columns'))} - {len(data.get('week_columns', []))} kolon")
        print(f"   total_materials: {data.get('total_materials', 0)}")
        print(f"   total_periods: {data.get('total_periods', 0)}")
        print(f"   data_points: {data.get('data_points', 0)}")
        
        # Eğer suppliers boşsa, supplier_mapping de boş olabilir
        if not data.get('suppliers'):
            print("   ⚠️ suppliers boş!")
        if not data.get('supplier_mapping'):
            print("   ⚠️ supplier_mapping boş!")
        
        materials = data.get('materials', [])
        period_count = data.get('total_periods', 0) or dataset.period_count or 0
        
        return {
            'has_data': True,
            'dataset_id': dataset.id,
            'upload_id': dataset.upload_id,
            'product_count': dataset.product_count,
            'period_count': dataset.period_count,
            'data_points': dataset.data_points,
            'source_type': dataset.source_type,
            'source_name': dataset.source_name,
            'created_at': dataset.created_at,
            'week_count': period_count,
            'material_count': len(materials),
            'is_active': dataset.is_active
        }


def get_active_dataset_service(db: Session) -> ActiveDatasetService:
    return ActiveDatasetService(db)