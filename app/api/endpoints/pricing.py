# app/api/endpoints/pricing.py - DÜZELTİLDİ

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import *
from app.auth import get_current_user
from app.services.pricing_engine import PricingEngine, get_pricing_engine
from app.services.dataset_builder import DatasetBuilder
from app.services.active_dataset import get_active_dataset_service
from app.schemas.credit import PricingResponse

router = APIRouter()


@router.get("/pricing/preview")
async def get_pricing_preview(
    endpoint: str = Query(..., description="Endpoint path (örn: /api/safety-stock/batch)"),
    dataset_id: Optional[int] = Query(None, description="Dataset ID (opsiyonel, yoksa aktif dataset kullanılır)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pricing preview - Bir endpoint'in maliyetini önceden gösterir.
    Kredi düşmez, sadece önizleme yapar.
    """
    try:
        # ✅ Dataset'i bul (önce belirtilen ID, yoksa aktif dataset)
        dataset = None
        builder = DatasetBuilder(db)
        
        if dataset_id:
            dataset = builder.get_dataset(dataset_id, current_user.id)
        
        if not dataset:
            # Aktif dataset'i al
            active_service = get_active_dataset_service(db)
            dataset = active_service.get_active_dataset(current_user.id)
        
        if not dataset:
            return {
                'error': 'Aktif dataset bulunamadı. Lütfen önce Excel yükleyip dataset oluşturun.',
                'has_dataset': False,
                'estimated_credit_cost': 0,
                'is_sufficient': False,
                'balance': current_user.token_balance
            }
        
        # ✅ Pricing engine ile maliyet hesapla
        pricing_engine = PricingEngine(db)
        preview = pricing_engine.get_endpoint_cost_preview(
            endpoint=endpoint,
            dataset_id=dataset.id,
            user_id=current_user.id
        )
        
        # ✅ Hata kontrolü
        if preview.get('error'):
            return {
                'error': preview['error'],
                'has_dataset': True,
                'dataset_id': dataset.id,
                'estimated_credit_cost': 0,
                'is_sufficient': False,
                'balance': current_user.token_balance
            }
        
        return {
            'success': True,
            'has_dataset': True,
            'dataset_id': dataset.id,
            'product_count': preview.get('product_count', 0),
            'period_count': preview.get('period_count', 0),
            'data_points': preview.get('data_points', 0),
            'estimated_credit_cost': preview.get('estimated_credit_cost', 0),
            'processing_score': preview.get('processing_score', 0),
            'calculation_method': preview.get('calculation_method', 'data_points'),
            'breakdown': preview.get('breakdown'),
            'is_sufficient': preview.get('is_sufficient', False),
            'balance': current_user.token_balance,
            'current_balance': current_user.token_balance,
        }
        
    except Exception as e:
        print(f"❌ Pricing preview hatası: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'has_dataset': False,
            'estimated_credit_cost': 0,
            'is_sufficient': False,
            'balance': current_user.token_balance
        }