from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import TokenCost, User, TokenHistory
from app.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================
# Admin Email Kontrol Fonksiyonu
# ============================================

def is_admin(user: User) -> bool:
    """Kullanıcının admin olup olmadığını kontrol et"""
    admin_emails = ["admin@stok.com", "admin@admin.com"]
    return user.email in admin_emails

# ============================================
# Pydantic Modelleri
# ============================================

class TokenCostCreate(BaseModel):
    endpoint: str
    method: str = "POST"
    cost: int = 1
    is_active: bool = True

class TokenCostUpdate(BaseModel):
    cost: Optional[int] = None
    is_active: Optional[bool] = None

class TokenCostResponse(BaseModel):
    id: int
    endpoint: str
    method: str
    cost: int
    is_active: bool
    updated_at: datetime

# ============================================
# Admin Token Cost Endpoint'leri
# ============================================

@router.get("/token-costs", response_model=List[TokenCostResponse])
async def get_token_costs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm token cost kayıtlarını listele"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    costs = db.query(TokenCost).order_by(TokenCost.endpoint).all()
    return costs


@router.post("/token-costs")
async def create_token_cost(
    request: TokenCostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni token cost kaydı oluştur"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    existing = db.query(TokenCost).filter(
        TokenCost.endpoint == request.endpoint,
        TokenCost.method == request.method
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Bu endpoint ({request.endpoint}) ve method ({request.method}) zaten kayıtlı"
        )
    
    token_cost = TokenCost(
        endpoint=request.endpoint,
        method=request.method,
        cost=request.cost,
        is_active=request.is_active
    )
    db.add(token_cost)
    db.commit()
    db.refresh(token_cost)
    
    return {"message": "Token cost başarıyla oluşturuldu", "data": token_cost}


@router.put("/token-costs/{cost_id}")
async def update_token_cost(
    cost_id: int,
    request: TokenCostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Token cost güncelle"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    token_cost = db.query(TokenCost).filter(TokenCost.id == cost_id).first()
    if not token_cost:
        raise HTTPException(status_code=404, detail="Token cost bulunamadı")
    
    if request.cost is not None:
        token_cost.cost = request.cost
    if request.is_active is not None:
        token_cost.is_active = request.is_active
    
    token_cost.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(token_cost)
    
    return {"message": "Token cost güncellendi", "data": token_cost}


@router.delete("/token-costs/{cost_id}")
async def delete_token_cost(
    cost_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Token cost sil"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    token_cost = db.query(TokenCost).filter(TokenCost.id == cost_id).first()
    if not token_cost:
        raise HTTPException(status_code=404, detail="Token cost bulunamadı")
    
    db.delete(token_cost)
    db.commit()
    
    return {"message": "Token cost silindi"}


@router.post("/token-costs/init-defaults")
async def init_default_token_costs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Varsayılan token cost kayıtlarını oluştur/güncelle (Admin)
    Sadece raporlama endpoint'leri için token düşer.
    Async status/result endpoint'leri ÜCRETSİZ.
    """
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    # ✅ SADECE RAPORLAMA ENDPOINT'LERİ (5 analiz sayfası)
    default_costs = [
        # 1. Talep Tahmini (Forecast)
        {"endpoint": "/api/forecast/batch", "method": "POST", "cost": 5, "is_active": True},
        {"endpoint": "/api/forecast/batch/async", "method": "POST", "cost": 8, "is_active": True},
        
        # 2. Emniyet Stoğu (Safety Stock)
        {"endpoint": "/api/safety-stock", "method": "POST", "cost": 3, "is_active": True},
        {"endpoint": "/api/safety-stock/batch/async", "method": "POST", "cost": 6, "is_active": True},
        
        # 3. Monte Carlo Simülasyonu
        {"endpoint": "/api/simulate", "method": "POST", "cost": 10, "is_active": True},
        {"endpoint": "/api/simulate/batch/async", "method": "POST", "cost": 15, "is_active": True},
        
        # 4. Backtest
        {"endpoint": "/api/backtest", "method": "POST", "cost": 15, "is_active": True},
        {"endpoint": "/api/backtest/batch/async", "method": "POST", "cost": 20, "is_active": True},
        
        # 5. Tedarikçi Analizi
        {"endpoint": "/api/supplier/optimize-shares", "method": "POST", "cost": 8, "is_active": True},
        {"endpoint": "/api/supplier/batch/async", "method": "POST", "cost": 12, "is_active": True},
        
        # 📋 Task Listesi (Ücretsiz)
        {"endpoint": "/api/tasks/async", "method": "GET", "cost": 0, "is_active": True},
    ]
    
    # ❌ Silinecek eski endpoint'ler (kullanılmayanlar)
    obsolete_endpoints = [
        "/api/pattern",
        "/api/forecast",
        "/api/risk/tail-risk",
        "/api/risk/cvar95",
        "/api/risk/service-level-gap",
    ]
    
    # Eski endpoint'leri pasif yap
    for endpoint in obsolete_endpoints:
        existing = db.query(TokenCost).filter(
            TokenCost.endpoint == endpoint
        ).all()
        for record in existing:
            record.is_active = False
            record.updated_at = datetime.utcnow()
            print(f"⏹️ Pasif yapıldı: {endpoint}")
    
    created_count = 0
    updated_count = 0
    
    for data in default_costs:
        existing = db.query(TokenCost).filter(
            TokenCost.endpoint == data["endpoint"],
            TokenCost.method == data["method"]
        ).first()
        
        if existing:
            existing.cost = data["cost"]
            existing.is_active = data["is_active"]
            existing.updated_at = datetime.utcnow()
            updated_count += 1
            print(f"🔄 Güncellendi: {data['endpoint']} → {data['cost']} Token")
        else:
            token_cost = TokenCost(
                endpoint=data["endpoint"],
                method=data["method"],
                cost=data["cost"],
                is_active=data["is_active"]
            )
            db.add(token_cost)
            created_count += 1
            print(f"✅ Eklendi: {data['endpoint']} → {data['cost']} Token")
    
    db.commit()
    
    # ✅ ÜCRETSİZ endpoint'leri güncelle
    free_endpoints = [
        "/api/upload",
        "/api/upload/status",
        "/api/cost",
        # ✅ Async status ve result endpoint'leri ücretsiz
        "/api/forecast/async/status/{task_id}",
        "/api/forecast/async/result/{task_id}",
    ]
    
    for endpoint in free_endpoints:
        records = db.query(TokenCost).filter(
            TokenCost.endpoint == endpoint
        ).all()
        if records:
            for record in records:
                record.cost = 0
                record.is_active = False  # ✅ Pasif yap (token kontrolünden muaf)
                record.updated_at = datetime.utcnow()
            print(f"🆓 Ücretsiz: {endpoint}")
        else:
            # Yoksa oluştur
            token_cost = TokenCost(
                endpoint=endpoint,
                method="GET",
                cost=0,
                is_active=False
            )
            db.add(token_cost)
            print(f"🆓 Ücretsiz eklendi: {endpoint}")
    
    db.commit()
    
    return {
        "message": "Token cost verileri güncellendi",
        "created": created_count,
        "updated": updated_count,
        "total": len(default_costs),
        "obsolete_disabled": len(obsolete_endpoints),
        "free_endpoints": free_endpoints,
        "details": {
            "active_analyses": [
                "Talep Tahmini (Forecast)",
                "Emniyet Stoğu (Safety Stock)",
                "Monte Carlo Simülasyonu",
                "Backtest",
                "Tedarikçi Analizi"
            ],
            "free_endpoints": free_endpoints
        }
    }


# ============================================
# Admin Dashboard İstatistikleri
# ============================================

@router.get("/dashboard/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin dashboard istatistikleri"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    total_users = db.query(User).count()
    total_token_costs = db.query(TokenCost).count()
    active_token_costs = db.query(TokenCost).filter(TokenCost.is_active == True).count()
    
    yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_tokens = db.query(TokenHistory).filter(
        TokenHistory.created_at >= yesterday
    ).all()
    
    total_spent = sum(t.cost for t in today_tokens)
    
    return {
        "total_users": total_users,
        "total_token_costs": total_token_costs,
        "active_token_costs": active_token_costs,
        "today_token_spent": total_spent,
        "today_transactions": len(today_tokens)
    }


@router.get("/token-history")
async def get_token_history(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Token harcama geçmişi (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    history = db.query(TokenHistory).order_by(
        TokenHistory.created_at.desc()
    ).limit(limit).all()
    
    return history


# ============================================
# Admin Kullanıcı Ekleme (Yardımcı)
# ============================================

@router.post("/create-admin")
async def create_admin_user(
    db: Session = Depends(get_db)
):
    """Admin kullanıcısı oluştur (Herkes erişebilir - sadece ilk kurulum için)"""
    from app.auth import get_password_hash
    
    admin_email = "admin@stok.com"
    existing = db.query(User).filter(User.email == admin_email).first()
    
    if existing:
        return {"message": "Admin kullanıcısı zaten var", "email": admin_email}
    
    admin = User(
        email=admin_email,
        hashed_password=get_password_hash("admin123"),
        full_name="Admin",
        company_name="Stok Yönetim",
        token_balance=999999
    )
    db.add(admin)
    db.commit()
    
    return {
        "message": "Admin kullanıcısı oluşturuldu",
        "email": admin_email,
        "password": "admin123"
    }