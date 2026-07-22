# app/api/endpoints/pricing.py - YENİ DOSYA
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.pricing_engine import PricingEngine
from app.services.dataset_builder import DatasetBuilder
from app.api.endpoints.upload import get_user_upload_data

router = APIRouter()


# app/api/endpoints/pricing.py - GÜNCELLENMİŞ

@router.get("/pricing/preview")
async def get_pricing_preview(
    endpoint: str,
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bir endpoint'in maliyetini önceden gösterir (kredi düşmez).
    """
    # 1. Dataset'i bul
    if dataset_id:
        builder = DatasetBuilder(db)
        dataset = builder.get_dataset(dataset_id, current_user.id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset bulunamadı")
    else:
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(
                status_code=404, 
                detail="Aktif dataset bulunamadı. Lütfen önce Excel yükleyin veya dataset_id belirtin."
            )
        
        upload_id = cached_data.get('upload_id')
        builder = DatasetBuilder(db)
        dataset = builder.get_dataset_by_upload_id(upload_id, current_user.id)
        
        if not dataset:
            dataset = builder.build_from_cache(
                user_id=current_user.id,
                cached_data=cached_data,
                upload_id=upload_id,
                source_type="excel",
                source_name=cached_data.get('file_name', 'unknown.xlsx')
            )
    
    # 2. Pricing Engine ile maliyet önizlemesi
    pricing_engine = PricingEngine(db)
    preview = pricing_engine.get_endpoint_cost_preview(
        endpoint=endpoint,
        dataset_id=dataset.id,
        user_id=current_user.id
    )
    
    # 🆕 DEBUG: preview içeriğini yazdır
    print(f"🔍 Pricing Preview: {preview}")
    
    return preview

