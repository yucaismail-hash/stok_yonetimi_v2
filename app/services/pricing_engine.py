# app/services/pricing_engine.py - TAM VE DOĞRU DOSYA
"""
Pricing Engine Servisi - Tüm fiyatlandırma mantığını yönetir.
Processing Score hesaplar, kredi düşer, loglar.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.dataset_builder import DatasetBuilder

from app.models import *
from app.schemas.credit import PricingRequest, PricingResponse

logger = logging.getLogger(__name__)


class PricingEngine:
    """
    Pricing Engine - Tek fiyatlandırma motoru.
    
    Görevleri:
    1. Dataset'i okur
    2. Endpoint profilini okur
    3. İşlem yükünü hesaplar (Processing Score)
    4. İşlem Kredisini hesaplar (Processing Score → Credit)
    5. Kullanıcının kredisini kontrol eder
    6. Krediyi düşer
    7. İşlemi loglar
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_processing_score(
        self,
        dataset: AnalysisDataset,
        endpoint_profile: EndpointProfile
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Processing Score hesaplar.
        
        Returns:
            Tuple[int, Dict[str, Any]]: (processing_score, breakdown)
        """
        dataset_config = endpoint_profile.dataset_config or {}
        
        # 🆕 DEBUG: endpoint_profile bilgilerini yazdır
        print(f"🔍 Endpoint: {endpoint_profile.endpoint}")
        print(f"🔍 dataset_config: {dataset_config}")
        print(f"🔍 dataset_config.get('datasets'): {dataset_config.get('datasets')}")
        
        if dataset_config and dataset_config.get('datasets'):
            # 🆕 Yeni sistem: Dataset Complexity Score
            builder = DatasetBuilder(self.db)
            dcs_score, breakdown = builder.get_dataset_complexity_score(dataset, dataset_config)
            
            # Algorithm weight'i uygula
            algorithm_weight = endpoint_profile.algorithm_weight or 1.0
            processing_score = int(dcs_score * algorithm_weight)
            
            print(f"✅ Dataset Complexity: dcs_score={dcs_score}, weight={algorithm_weight}, processing_score={processing_score}")
            
            return processing_score, {
                "method": "dataset_complexity",
                "dataset_complexity_score": dcs_score,
                "algorithm_weight": algorithm_weight,
                "breakdown": breakdown
            }
        else:
            # ⏳ Eski sistem: Data Points
            data_points = dataset.data_points or 0
            algorithm_weight = endpoint_profile.algorithm_weight or 1.0
            processing_score = int(data_points * algorithm_weight)
            
            print(f"⏳ Data Points: data_points={data_points}, weight={algorithm_weight}, processing_score={processing_score}")
            
            return processing_score, {
                "method": "data_points",
                "data_points": data_points,
                "algorithm_weight": algorithm_weight
            }

    def get_credit_cost(self, processing_score: int) -> Tuple[int, Optional[ProcessingScoreRange]]:
        """
        Processing Score'dan İşlem Kredisini hesaplar.
        
        Args:
            processing_score: Hesaplanan Processing Score
        
        Returns:
            Tuple[int, Optional[ProcessingScoreRange]]: (credit_cost, range_record)
        """
        # Aktif aralıkları bul
        ranges = self.db.query(ProcessingScoreRange).filter(
            ProcessingScoreRange.is_active == True
        ).order_by(
            ProcessingScoreRange.min_score
        ).all()
        
        if not ranges:
            logger.warning("⚠️ ProcessingScoreRange tablosu boş! Varsayılan değer kullanılıyor.")
            # Varsayılan aralık
            return 3, None
        
        # Score'a uygun aralığı bul
        for range_record in ranges:
            if range_record.min_score <= processing_score <= range_record.max_score:
                return range_record.credit_cost, range_record
        
        # Hiçbir aralığa uymuyorsa en yüksek aralığı kullan
        last_range = ranges[-1]
        if processing_score > last_range.max_score:
            return last_range.credit_cost, last_range
        
        # En düşük aralığı kullan (0-20000)
        first_range = ranges[0]
        if processing_score < first_range.min_score:
            return first_range.credit_cost, first_range
        
        # Fallback
        return 3, None
    
    def get_endpoint_profile(self, endpoint: str, method: str = "POST") -> Optional[EndpointProfile]:
        """
        Endpoint profilini getirir.
        """
        return self.db.query(EndpointProfile).filter(
            EndpointProfile.endpoint == endpoint,
            EndpointProfile.method == method,
            EndpointProfile.is_active == True
        ).first()
    
    def process_request(
        self,
        request: PricingRequest,
        start_time: Optional[float] = None
    ) -> PricingResponse:
        """
        Ana fiyatlandırma işlemi.
        
        Akış:
        1. Dataset'i kontrol et
        2. Endpoint profilini kontrol et
        3. Processing Score hesapla
        4. İşlem Kredisini hesapla
        5. Kullanıcı bakiyesini kontrol et
        6. Krediyi düş
        7. Logla
        8. Yanıtı döndür
        
        Args:
            request: PricingRequest (endpoint, dataset_id, user_id)
            start_time: İşlem başlangıç zamanı (elapsed_time için)
        
        Returns:
            PricingResponse
        """
        start = start_time or time.time()
        
        # 1. Kullanıcıyı kontrol et
        user = self.db.query(User).filter(User.id == request.user_id).first()
        if not user:
            return PricingResponse(
                success=False,
                dataset_id=request.dataset_id,
                endpoint=request.endpoint,
                product_count=0,
                period_count=0,
                data_points=0,
                algorithm_weight=0,
                processing_score=0,
                credit_cost=0,
                balance_before=0,
                balance_after=0,
                is_sufficient=False,
                message="Kullanıcı bulunamadı"
            )
        
        # 2. Dataset'i kontrol et
        dataset = self.db.query(AnalysisDataset).filter(
            AnalysisDataset.id == request.dataset_id,
            AnalysisDataset.user_id == request.user_id,
            AnalysisDataset.is_active == True
        ).first()
        
        if not dataset:
            return PricingResponse(
                success=False,
                dataset_id=request.dataset_id,
                endpoint=request.endpoint,
                product_count=0,
                period_count=0,
                data_points=0,
                algorithm_weight=0,
                processing_score=0,
                credit_cost=0,
                balance_before=user.token_balance,
                balance_after=user.token_balance,
                is_sufficient=False,
                message="Dataset bulunamadı veya aktif değil"
            )
        
        # 3. Endpoint profilini kontrol et
        endpoint_profile = self.get_endpoint_profile(request.endpoint)
        if not endpoint_profile:
            # Profil yoksa varsayılan değerler kullan
            logger.warning(f"⚠️ Endpoint profili bulunamadı: {request.endpoint}, varsayılan değerler kullanılıyor")
            algorithm_weight = 1.0
            base_credit = 1
            dataset_config = {}
        else:
            algorithm_weight = endpoint_profile.algorithm_weight
            base_credit = endpoint_profile.base_credit
            dataset_config = endpoint_profile.dataset_config or {}
        
        # 4. Processing Score hesapla
        if endpoint_profile:
            processing_score, breakdown = self.calculate_processing_score(dataset, endpoint_profile)
        else:
            processing_score = dataset.data_points or 0
            breakdown = {"method": "data_points", "data_points": processing_score, "algorithm_weight": 1.0}
        
        # 5. İşlem Kredisini hesapla
        credit_cost, score_range = self.get_credit_cost(processing_score)
        
        # Base credit ekle (varsa)
        if endpoint_profile and endpoint_profile.base_credit > 1:
            credit_cost = max(1, credit_cost + endpoint_profile.base_credit - 1)
        
        # 6. Kullanıcı bakiyesini kontrol et
        balance_before = user.token_balance
        is_sufficient = balance_before >= credit_cost
        
        if not is_sufficient:
            return PricingResponse(
                success=False,
                dataset_id=dataset.id,
                endpoint=request.endpoint,
                product_count=dataset.product_count,
                period_count=dataset.period_count,
                data_points=dataset.data_points,
                algorithm_weight=algorithm_weight,
                processing_score=processing_score,
                credit_cost=credit_cost,
                balance_before=balance_before,
                balance_after=balance_before,
                is_sufficient=False,
                message=f"Yetersiz kredi! Gerekli: {credit_cost}, Mevcut: {balance_before}",
                calculation_method=breakdown.get("method") if breakdown else "data_points",
                breakdown=breakdown.get("breakdown") if breakdown else None
            )
        
        # 7. Krediyi düş
        user.token_balance -= credit_cost
        self.db.commit()
        
        # 8. İşlemi logla (ProcessingTransaction)
        elapsed_time_ms = (time.time() - start) * 1000
        
        transaction = ProcessingTransaction(
            user_id=user.id,
            dataset_id=dataset.id,
            endpoint=request.endpoint,
            processing_score=processing_score,
            credit_cost=credit_cost,
            balance_after=user.token_balance,
            elapsed_time_ms=elapsed_time_ms,
            avg_time_per_unit_ms=elapsed_time_ms / processing_score if processing_score > 0 else None,
            status="completed"
        )
        self.db.add(transaction)
        
        # 9. Eski TokenHistory'ye de logla (uyumluluk için)
        history = TokenHistory(
            user_id=user.id,
            endpoint=request.endpoint,
            cost=credit_cost,
            balance_after=user.token_balance
        )
        self.db.add(history)
        
        self.db.commit()
        
        logger.info(
            f"✅ Pricing işlemi tamamlandı: "
            f"User={user.id}, Endpoint={request.endpoint}, "
            f"Score={processing_score}, Cost={credit_cost}, "
            f"Balance={user.token_balance}, Elapsed={elapsed_time_ms:.2f}ms"
        )
        
        # 10. Yanıtı döndür
        return PricingResponse(
            success=True,
            dataset_id=dataset.id,
            endpoint=request.endpoint,
            product_count=dataset.product_count,
            period_count=dataset.period_count,
            data_points=dataset.data_points,
            algorithm_weight=algorithm_weight,
            processing_score=processing_score,
            credit_cost=credit_cost,
            balance_before=balance_before,
            balance_after=user.token_balance,
            is_sufficient=True,
            message="İşlem başarılı",
            calculation_method=breakdown.get("method") if breakdown else "data_points",
            breakdown=breakdown.get("breakdown") if breakdown else None
        )
    
    def get_endpoint_cost_preview(
        self,
        endpoint: str,
        dataset_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Endpoint maliyetini önceden hesaplar (kredi düşmez).
        🆕 Dataset Complexity Score desteği eklendi.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': 'Kullanıcı bulunamadı'}
        
        dataset = self.db.query(AnalysisDataset).filter(
            AnalysisDataset.id == dataset_id,
            AnalysisDataset.user_id == user_id
        ).first()
        
        if not dataset:
            return {'error': 'Dataset bulunamadı'}
        
        endpoint_profile = self.get_endpoint_profile(endpoint)
        
        # 🆕 DEBUG: endpoint_profile bilgilerini yazdır
        print(f"🔍 get_endpoint_cost_preview - endpoint: {endpoint}")
        print(f"🔍 get_endpoint_cost_preview - endpoint_profile: {endpoint_profile}")
        if endpoint_profile:
            print(f"🔍 get_endpoint_cost_preview - dataset_config: {endpoint_profile.dataset_config}")
        
        if not endpoint_profile:
            algorithm_weight = 1.0
            base_credit = 1
            dataset_config = {}
        else:
            algorithm_weight = endpoint_profile.algorithm_weight
            base_credit = endpoint_profile.base_credit
            dataset_config = endpoint_profile.dataset_config or {}
        
        # 🆕 Dataset Complexity Score hesapla
        builder = DatasetBuilder(self.db)
        
        print(f"🔍 dataset_config: {dataset_config}")
        print(f"🔍 dataset_config.get('datasets'): {dataset_config.get('datasets') if dataset_config else 'None'}")
        
        if dataset_config and dataset_config.get('datasets'):
            dcs_score, breakdown = builder.get_dataset_complexity_score(dataset, dataset_config)
            processing_score = int(dcs_score * algorithm_weight)
            method = "dataset_complexity"
            print(f"✅ Dataset Complexity: dcs_score={dcs_score}, weight={algorithm_weight}, processing_score={processing_score}")
            print(f"✅ breakdown: {breakdown}")
        else:
            data_points = dataset.data_points or 0
            processing_score = int(data_points * algorithm_weight)
            method = "data_points"
            breakdown = None
            print(f"⏳ Data Points: data_points={data_points}, weight={algorithm_weight}, processing_score={processing_score}")
        
        credit_cost, _ = self.get_credit_cost(processing_score)
        
        if endpoint_profile and endpoint_profile.base_credit > 1:
            credit_cost = max(1, credit_cost + endpoint_profile.base_credit - 1)
        
        return {
            'endpoint': endpoint,
            'dataset_id': dataset.id,
            'product_count': dataset.product_count,
            'period_count': dataset.period_count,
            'data_points': dataset.data_points,
            'algorithm_weight': algorithm_weight,
            'processing_score': processing_score,
            'estimated_credit_cost': credit_cost,
            'current_balance': user.token_balance,
            'is_sufficient': user.token_balance >= credit_cost,
            'calculation_method': method,
            'breakdown': breakdown
        }


def get_pricing_engine(db: Session) -> PricingEngine:
    """PricingEngine instance'ı oluşturur (dependency injection için)"""
    return PricingEngine(db)