# app/api/dependencies.py
"""
API Bağımlılıkları - Endpoint'lerin kullanacağı ortak dependency'ler
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AnalysisDataset
from app.services.dataset_builder import DatasetBuilder, get_dataset_builder
from app.services.pricing_engine import PricingEngine, get_pricing_engine
from app.auth import get_current_user
from app.schemas.credit import PricingRequest, PricingResponse


def get_active_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AnalysisDataset:
    """
    Aktif dataset'i kontrol eder ve getirir.
    Endpoint'lerde dataset doğrulaması için kullanılır.
    """
    dataset = db.query(AnalysisDataset).filter(
        AnalysisDataset.id == dataset_id,
        AnalysisDataset.user_id == current_user.id,
        AnalysisDataset.is_active == True
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset bulunamadı veya aktif değil"
        )
    
    return dataset


def get_dataset_from_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AnalysisDataset:
    """
    Upload ID'ye göre aktif dataset'i getirir.
    """
    dataset = db.query(AnalysisDataset).filter(
        AnalysisDataset.upload_id == upload_id,
        AnalysisDataset.user_id == current_user.id,
        AnalysisDataset.is_active == True
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu upload_id ile eşleşen aktif dataset bulunamadı"
        )
    
    return dataset


def get_or_create_dataset_from_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AnalysisDataset:
    """
    Upload ID'ye göre dataset arar, yoksa cache'den oluşturur.
    """
    from app.api.endpoints.upload import get_user_upload_data
    
    # 1. Önce veritabanında ara
    dataset = db.query(AnalysisDataset).filter(
        AnalysisDataset.upload_id == upload_id,
        AnalysisDataset.user_id == current_user.id,
        AnalysisDataset.is_active == True
    ).first()
    
    if dataset:
        return dataset
    
    # 2. Yoksa cache'den oluştur
    cached_data = get_user_upload_data(current_user.id)
    if not cached_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cache'de veri bulunamadı. Lütfen önce Excel yükleyin."
        )
    
    builder = DatasetBuilder(db)
    new_dataset = builder.build_from_cache(
        user_id=current_user.id,
        cached_data=cached_data,
        upload_id=upload_id,
        source_type="excel",
        source_name=cached_data.get('file_name', 'unknown.xlsx')
    )
    
    return new_dataset


def process_pricing(
    endpoint: str,
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PricingResponse:
    """
    Pricing işlemini gerçekleştirir.
    Tüm endpoint'ler bu dependency'yi kullanarak token kontrolü yapar.
    """
    pricing_engine = PricingEngine(db)
    
    request = PricingRequest(
        endpoint=endpoint,
        dataset_id=dataset_id,
        user_id=current_user.id
    )
    
    response = pricing_engine.process_request(request)
    
    if not response.is_sufficient:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=response.message or "Yetersiz kredi"
        )
    
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message or "Pricing işlemi başarısız"
        )
    
    return response


def process_pricing_with_dataset(
    endpoint: str,
    dataset: AnalysisDataset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PricingResponse:
    """
    Dataset objesi ile pricing işlemini gerçekleştirir.
    """
    pricing_engine = PricingEngine(db)
    
    request = PricingRequest(
        endpoint=endpoint,
        dataset_id=dataset.id,
        user_id=current_user.id
    )
    
    response = pricing_engine.process_request(request)
    
    if not response.is_sufficient:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=response.message or "Yetersiz kredi"
        )
    
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message or "Pricing işlemi başarısız"
        )
    
    return response