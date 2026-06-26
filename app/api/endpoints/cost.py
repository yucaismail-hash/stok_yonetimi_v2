from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import TokenCost

router = APIRouter()

@router.get("/cost")
async def get_cost(
    endpoint: Optional[str] = Query(None, description="Maliyeti sorgulanacak endpoint"),
    method: Optional[str] = Query("POST", description="HTTP metodu (GET, POST, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Belirtilen endpoint'in token maliyetini döndürür.
    
    - endpoint: /api/forecast/batch, /api/forecast/batch/async, /api/upload/status, vb.
    - method: GET, POST, PUT, DELETE (varsayılan: POST)
    
    Örnek: /api/cost?endpoint=/api/forecast/batch/async&method=POST
    """
    if not endpoint:
        # Eğer endpoint belirtilmemişse, varsayılan olarak forecast/batch döndür
        endpoint = "/api/forecast/batch"
    
    # Veritabanından token cost'u sorgula
    cost_record = db.query(TokenCost).filter(
        TokenCost.endpoint == endpoint,
        TokenCost.method == method,
        TokenCost.is_active == True
    ).first()
    
    if cost_record:
        return {
            "cost": cost_record.cost,
            "endpoint": cost_record.endpoint,
            "method": cost_record.method,
            "is_active": cost_record.is_active
        }
    
    # Eğer kayıt bulunamazsa, endpoint'i normalize ederek tekrar dene
    # Örneğin: /api/forecast/batch/async -> /api/forecast/batch
    if endpoint.endswith("/async"):
        fallback_endpoint = endpoint.replace("/async", "")
        cost_record = db.query(TokenCost).filter(
            TokenCost.endpoint == fallback_endpoint,
            TokenCost.method == method,
            TokenCost.is_active == True
        ).first()
        
        if cost_record:
            return {
                "cost": cost_record.cost,
                "endpoint": fallback_endpoint,
                "method": cost_record.method,
                "is_active": cost_record.is_active,
                "note": f"'{endpoint}' için kayıt bulunamadı, '{fallback_endpoint}' maliyeti kullanılıyor"
            }
    
    # Hiçbir kayıt bulunamazsa varsayılan değer döndür
    return {
        "cost": 8,
        "endpoint": endpoint,
        "method": method,
        "is_active": True,
        "note": "Varsayılan maliyet (8) kullanılıyor"
    }


@router.get("/costs")
async def get_all_costs(
    db: Session = Depends(get_db)
):
    """Tüm aktif token cost'ları listele"""
    costs = db.query(TokenCost).filter(
        TokenCost.is_active == True
    ).order_by(TokenCost.endpoint).all()
    
    return [
        {
            "endpoint": c.endpoint,
            "method": c.method,
            "cost": c.cost
        }
        for c in costs
    ]