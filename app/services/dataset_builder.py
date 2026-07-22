# app/services/dataset_builder.py - GÜNCELLENMİŞ

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import AnalysisDataset, User
from app.schemas.dataset import DatasetCreate, DatasetResponse

logger = logging.getLogger(__name__)
TURKEY_TZ = timezone(timedelta(hours=3))

class DatasetBuilder:
    """
    Dataset Builder - Veri kaynağından bağımsız olarak ortak Dataset oluşturur.
    
    Desteklenen kaynaklar:
    - Excel (upload.py'den gelen cache verisi)
    - API (REST API entegrasyonu)
    - ERP (SAP, Logo, Mikro, Nebim)
    - CSV
    """
    
    def __init__(self, db: Session):
        """DatasetBuilder constructor - db parametresi alır."""
        self.db = db
    
    def build_from_cache(
        self,
        user_id: int,
        cached_data: Dict[str, Any],
        upload_id: Optional[str] = None,
        source_type: str = "excel",
        source_name: Optional[str] = None
    ) -> AnalysisDataset:
        """
        Cache'den gelen verilerden Dataset oluşturur.
        
        Args:
            user_id: Kullanıcı ID
            cached_data: upload.py'deki cache verisi
            upload_id: Upload ID (opsiyonel)
            source_type: Veri kaynağı tipi (excel, api, erp, csv)
            source_name: Kaynak adı (opsiyonel)
        
        Returns:
            AnalysisDataset: Oluşturulan dataset
        """
        # 1. Verileri çıkar
        materials = cached_data.get('materials', [])
        suppliers = cached_data.get('suppliers', {})
        supplier_mapping = cached_data.get('supplier_mapping', {})
        week_columns = cached_data.get('week_columns', [])
        
        # 2. Product Count hesapla
        product_count = len(materials)
        
        # 3. Period Count hesapla (en uzun historical_demand)
        period_count = 0
        for material in materials:
            demand = material.get('historical_demand', [])
            if not demand:
                demand = material.get('weekly_data', [])
            if not demand:
                # W1, W2... formatında olabilir
                w_cols = [material.get(f'W{i}') for i in range(1, 20) if material.get(f'W{i}') is not None]
                if w_cols:
                    demand = w_cols
            if len(demand) > period_count:
                period_count = len(demand)
        
        # 4. Data Points hesapla (ProductCount × PeriodCount)
        data_points = product_count * period_count
        
        # 5. Dataset verisini hazırla
        dataset_data = {
            'materials': materials,
            'suppliers': suppliers,
            'supplier_mapping': supplier_mapping,
            'week_columns': week_columns,
            'total_materials': product_count,
            'total_periods': period_count,
            'data_points': data_points,
            'source_type': source_type,
            'source_name': source_name,
            'upload_id': upload_id,
            'created_from': 'cache'
        }
        
        now_turkey = datetime.now(TURKEY_TZ)

        # 6. Veritabanına kaydet
        dataset = AnalysisDataset(
            upload_id=upload_id,
            user_id=user_id,
            product_count=product_count,
            period_count=period_count,
            data_points=data_points,
            dataset_data=dataset_data,
            source_type=source_type,
            source_name=source_name,
            is_active=True,
            created_at=now_turkey,          # ✅ Türkiye saati
            expires_at=datetime.utcnow() + timedelta(days=30)  # 30 gün geçerli
        )
        
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        
        logger.info(
            f"✅ Dataset oluşturuldu: ID={dataset.id}, "
            f"Ürün={product_count}, Dönem={period_count}, "
            f"Data Points={data_points}, Kaynak={source_type}"
        )
        
        return dataset
    
    def build_from_materials(
        self,
        user_id: int,
        materials: List[Dict[str, Any]],
        suppliers: Optional[Dict[str, Any]] = None,
        supplier_mapping: Optional[Dict[str, Any]] = None,
        week_columns: Optional[List[str]] = None,
        upload_id: Optional[str] = None,
        source_type: str = "api",
        source_name: Optional[str] = None
    ) -> AnalysisDataset:
        """
        Doğrudan materials listesinden Dataset oluşturur.
        API veya ERP entegrasyonları için kullanılır.
        """
        cached_data = {
            'materials': materials,
            'suppliers': suppliers or {},
            'supplier_mapping': supplier_mapping or {},
            'week_columns': week_columns or [],
            'upload_id': upload_id
        }
        
        return self.build_from_cache(
            user_id=user_id,
            cached_data=cached_data,
            upload_id=upload_id,
            source_type=source_type,
            source_name=source_name
        )
    
    def get_dataset(self, dataset_id: int, user_id: int) -> Optional[AnalysisDataset]:
        """Dataset ID'ye göre dataset getirir (kullanıcı doğrulamalı)"""
        return self.db.query(AnalysisDataset).filter(
            AnalysisDataset.id == dataset_id,
            AnalysisDataset.user_id == user_id,
            AnalysisDataset.is_active == True
        ).first()
    
    def get_dataset_by_upload_id(self, upload_id: str, user_id: int) -> Optional[AnalysisDataset]:
        """Upload ID'ye göre dataset getirir (kullanıcı doğrulamalı)"""
        return self.db.query(AnalysisDataset).filter(
            AnalysisDataset.upload_id == upload_id,
            AnalysisDataset.user_id == user_id,
            AnalysisDataset.is_active == True
        ).first()
    
    def get_active_datasets(self, user_id: int, limit: int = 10) -> List[AnalysisDataset]:
        """Kullanıcının aktif dataset'lerini getirir"""
        return self.db.query(AnalysisDataset).filter(
            AnalysisDataset.user_id == user_id,
            AnalysisDataset.is_active == True
        ).order_by(
            AnalysisDataset.created_at.desc()
        ).limit(limit).all()
    
    def deactivate_dataset(self, dataset_id: int, user_id: int) -> bool:
        """Dataset'i pasifleştirir"""
        dataset = self.get_dataset(dataset_id, user_id)
        if not dataset:
            return False
        
        dataset.is_active = False
        self.db.commit()
        return True
    
    def get_dataset_stats(self, dataset: AnalysisDataset) -> Dict[str, Any]:
        """Dataset istatistiklerini döndürür"""
        return {
            'id': dataset.id,
            'product_count': dataset.product_count,
            'period_count': dataset.period_count,
            'data_points': dataset.data_points,
            'source_type': dataset.source_type,
            'source_name': dataset.source_name,
            'created_at': dataset.created_at,
            'is_active': dataset.is_active
        }

    def get_dataset_complexity_score(
        self,
        dataset: AnalysisDataset,
        dataset_config: Dict[str, Any]
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Dataset Complexity Score (DCS) hesaplar.
        """
        print(f"🔍 get_dataset_complexity_score - dataset_config: {dataset_config}")
        print(f"🔍 get_dataset_complexity_score - dataset_config type: {type(dataset_config)}")
        
        if not dataset_config or not dataset_config.get('datasets'):
            print("⚠️ dataset_config boş veya datasets yok! Varsayılan data_points kullanılıyor.")
            data_points = dataset.data_points or 0
            return data_points, {
                "data_points": {"score": data_points, "table": "materials", "row_count": 0, "weight": 1.0},
                "total": data_points
            }
        
        datasets = dataset_config.get('datasets', [])
        dataset_data = dataset.dataset_data or {}
        
        print(f"🔍 datasets: {datasets}")
        print(f"🔍 dataset_data keys: {dataset_data.keys() if dataset_data else 'None'}")
        
        total_score = 0
        breakdown = {}
        
        for ds_config in datasets:
            table_name = ds_config.get('table', '')
            weight = ds_config.get('weight', 1.0)
            ds_type = ds_config.get('type', 'data_points')
            row_count = 0
            
            print(f"🔍 Processing: table={table_name}, weight={weight}, type={ds_type}")
            
            # ✅ Tablo adına göre veriyi al
            if table_name == 'materials':
                materials = dataset_data.get('materials', [])
                period_count = dataset_data.get('total_periods', 0) or dataset.period_count or 0
                product_count = len(materials)
                
                # Data Points: product_count × period_count
                if ds_type == 'data_points':
                    row_count = product_count * period_count
                else:
                    row_count = product_count
                    
                print(f"📊 materials: product_count={product_count}, period_count={period_count}, row_count={row_count}")
                
            elif table_name == 'material_suppliers':
                supplier_mapping = dataset_data.get('supplier_mapping', {})
                row_count = sum(len(mappings) for mappings in supplier_mapping.values())
                print(f"🔗 material_suppliers: row_count={row_count}")
                
            elif table_name == 'suppliers':
                suppliers = dataset_data.get('suppliers', {})
                row_count = len(suppliers)
                print(f"📋 suppliers: row_count={row_count}")
                
            else:
                # Bilinmeyen tablo - dataset_data içinde ara
                row_count = len(dataset_data.get(table_name, []))
                print(f"❓ unknown table {table_name}: row_count={row_count}")
            
            # Score hesapla
            score = int(row_count * weight)
            total_score += score
            
            breakdown[ds_type] = {
                "score": score,
                "table": table_name,
                "row_count": row_count,
                "weight": weight
            }
        
        breakdown["total"] = total_score
        print(f"✅ Dataset Complexity Score: {total_score}, breakdown: {breakdown}")
        return total_score, breakdown

def get_dataset_builder(db: Session) -> DatasetBuilder:
    """DatasetBuilder instance'ı oluşturur (dependency injection için)"""
    return DatasetBuilder(db)