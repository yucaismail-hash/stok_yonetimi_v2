# app/services/dataset_builder.py
"""
Dataset Builder - Veri kaynağından bağımsız olarak Dataset oluşturur.
Dataset Gate: validation sonucu kontrol edilir, can_proceed=False ise hata fırlatılır.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import *
from app.schemas.dataset import DatasetCreate, DatasetResponse

logger = logging.getLogger(__name__)
TURKEY_TZ = timezone(timedelta(hours=3))


class DatasetBuilder:
    """
    Dataset Builder - Veri kaynağından bağımsız olarak Dataset oluşturur.
    Desteklenen kaynaklar:
    - Excel (upload.py'den gelen cache verisi)
    - API (REST API entegrasyonu)
    - ERP (SAP, Logo, Mikro, Nebim)
    - CSV
    """

    def __init__(self, db: Session):
        self.db = db

    def build_from_cache(
        self,
        user_id: int,
        cached_data: Dict[str, Any],
        upload_id: Optional[str] = None,
        source_type: str = "excel",
        source_name: Optional[str] = None,
        validation_result: Optional[Dict[str, Any]] = None  # Dataset Gate için
    ) -> AnalysisDataset:
        """
        Cache'den gelen verilerden Dataset oluşturur.

        Args:
            user_id: Kullanıcı ID
            cached_data: upload.py'deki cache verisi
            upload_id: Upload ID (opsiyonel)
            source_type: Veri kaynağı tipi (excel, api, erp, csv)
            source_name: Kaynak adı (opsiyonel)
            validation_result: Validation sonucu (Dataset Gate için)

        Returns:
            AnalysisDataset: Oluşturulan dataset

        Raises:
            ValueError: can_proceed=False ise veya dataset semantically invalid ise
        """
        # ============================================================
        # DATASET GATE: validation sonucu kontrol et
        # ============================================================
        if validation_result:
            can_proceed = validation_result.get('can_proceed', True)
            if not can_proceed:
                # Kritik hataları topla
                critical_errors = []
                data_quality = validation_result.get('data_quality', {})
                
                # Structural errors
                for err in data_quality.get('structural_errors', []):
                    if err.get('severity') == 'critical':
                        critical_errors.append(f"Yapısal Hata: {err.get('message', '')}")
                
                # Missing data (critical olanlar)
                for err in data_quality.get('missing_data', []):
                    if err.get('severity') == 'critical':
                        critical_errors.append(f"Eksik Veri: {err.get('message', '')}")
                
                # Data type errors
                for err in data_quality.get('data_type_errors', []):
                    if err.get('severity') == 'critical':
                        critical_errors.append(f"Veri Tipi Hatası: {err.get('message', '')}")
                
                # Business rule errors
                for err in data_quality.get('business_rule_errors', []):
                    if err.get('severity') == 'critical':
                        critical_errors.append(f"İş Kuralı Hatası: {err.get('message', '')}")
                
                error_msg = f"Dataset oluşturulamıyor. Kritik hatalar: {', '.join(critical_errors[:5])}"
                logger.error(f"❌ Dataset Gate: {error_msg}")
                raise ValueError(error_msg)
        else:
            # Validation sonucu yoksa uyarı ver ama engelleme
            logger.warning("⚠️ Dataset Gate: validation sonucu sağlanmadı, devam ediliyor.")

        # ============================================================
        # 1. Verileri çıkar
        # ============================================================
        materials = cached_data.get('materials', [])
        suppliers = cached_data.get('suppliers', {})
        supplier_mapping = cached_data.get('supplier_mapping', {})
        week_columns = cached_data.get('week_columns', [])

        # 2. Product Count hesapla
        product_count = len(materials)

        # 3. Period Count hesapla (historical_demand veya weekly_data)
        period_count = 0
        for material in materials:
            # Önce weekly_data dene
            demand = material.get('weekly_data', [])
            if not demand or len(demand) == 0:
                # Sonra historical_demand dene
                demand = material.get('historical_demand', [])
            if not demand or len(demand) == 0:
                # W1, W2... formatında olabilir
                w_cols = []
                for i in range(1, 53):  # maksimum 52 hafta
                    key = f'W{i}'
                    if key in material:
                        w_cols.append(material[key])
                if w_cols:
                    demand = w_cols
            
            # Sadece None olmayan değerleri say (0 da geçerli)
            valid_demand = [d for d in demand if d is not None]
            if len(valid_demand) > period_count:
                period_count = len(valid_demand)

        
        print("========== DATASET DEBUG ==========")
        print("cached_data keys:", cached_data.keys())

        print("materials len:", len(materials))

        if materials:
            print(materials[0].keys())

            print("weekly_data =", materials[0].get("weekly_data"))

            print("historical_demand =", materials[0].get("historical_demand"))

        print("===================================")
        
        # ✅ Eğer period_count 0 ise, W kolonlarını doğrudan kontrol et
        if period_count == 0:
            print("🔍 Period count 0, W kolonlarını doğrudan kontrol ediyorum...")
            for material in materials:
                # W kolonlarını say
                w_count = 0
                for key in material.keys():
                    if key.startswith('W'):
                        try:
                            week_num = int(key[1:])
                            if 1 <= week_num <= 52:
                                w_count += 1
                        except:
                            pass
                if w_count > period_count:
                    period_count = w_count
                    print(f"   W kolonları bulundu: {period_count} adet")
        
        # ✅ Eğer hala period_count 0 ise hata fırlat
        if period_count == 0:
            error_msg = "Geçmiş talep verisi bulunamadı. Dataset oluşturulamaz."
            logger.error(f"❌ Semantic Validation: {error_msg}")
            raise ValueError(error_msg)

        # 4. Data Points hesapla (ProductCount × PeriodCount)
        data_points = product_count * period_count

        # 5. SEMANTIC VALIDATION: Eğer period_count 0 ise hata fırlat
        if period_count == 0:
            error_msg = "Geçmiş talep verisi bulunamadı. Dataset oluşturulamaz."
            logger.error(f"❌ Semantic Validation: {error_msg}")
            raise ValueError(error_msg)


        # 6. Dataset verisini hazırla
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
            'created_from': 'cache',
            'validation_passed': True if validation_result else False
        }

        now_turkey = datetime.now(TURKEY_TZ)

        # 7. Veritabanına kaydet
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
            created_at=now_turkey,
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
        suppliers: Optional[Dict[str, Any]] = None,  # ✅ dict bekliyor
        supplier_mapping: Optional[Dict[str, Any]] = None,  # ✅ dict bekliyor
        week_columns: Optional[List[str]] = None,
        upload_id: Optional[str] = None,
        source_type: str = "api",
        source_name: Optional[str] = None,
        validation_result: Optional[Dict[str, Any]] = None
    ) -> AnalysisDataset:
        """
        Doğrudan materials listesinden Dataset oluşturur.
        """
        cached_data = {
            'materials': materials,
            'suppliers': suppliers or {},      # ✅ dict olarak kaydediliyor
            'supplier_mapping': supplier_mapping or {},  # ✅ dict olarak kaydediliyor
            'week_columns': week_columns or [],
            'upload_id': upload_id
        }
        print("=========== CACHE ===========")

        print(cached_data)

        print(cached_data["suppliers"])

        print(cached_data["supplier_mapping"])

        return self.build_from_cache(
            user_id=user_id,
            cached_data=cached_data,
            upload_id=upload_id,
            source_type=source_type,
            source_name=source_name,
            validation_result=validation_result
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
        Pricing Engine tarafından kullanılır.
        """
        print(f"🔍 get_dataset_complexity_score - dataset_config: {dataset_config}")
        
        if not dataset_config or not dataset_config.get('datasets'):
            print("⚠️ dataset_config boş veya datasets yok! Varsayılan data_points kullanılıyor.")
            data_points = dataset.data_points or 0
            return data_points, {
                "data_points": {"score": data_points, "table": "materials", "row_count": 0, "weight": 1.0},
                "total": data_points
            }

        datasets = dataset_config.get('datasets', [])
        dataset_data = dataset.dataset_data or {}

        total_score = 0
        breakdown = {}

        for ds_config in datasets:
            table_name = ds_config.get('table', '')
            weight = ds_config.get('weight', 1.0)
            ds_type = ds_config.get('type', 'data_points')
            row_count = 0

            if table_name == 'materials':
                materials = dataset_data.get('materials', [])
                period_count = dataset_data.get('total_periods', 0) or dataset.period_count or 0
                product_count = len(materials)
                if ds_type == 'data_points':
                    row_count = product_count * period_count
                else:
                    row_count = product_count

            elif table_name == 'material_suppliers':
                supplier_mapping = dataset_data.get('supplier_mapping', {})
                row_count = sum(len(mappings) for mappings in supplier_mapping.values())

            elif table_name == 'suppliers':
                suppliers = dataset_data.get('suppliers', {})
                row_count = len(suppliers)

            else:
                row_count = len(dataset_data.get(table_name, []))

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