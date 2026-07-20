from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import (
    TokenCost, 
    User, 
    TokenHistory, 
    CreditPackage, 
    CreditTransaction,
    Notification
)
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
# 🆕 CREDIT PACKAGE MODELLERİ
# ============================================

class CreditPackageCreate(BaseModel):
    polar_product_id: str
    name: str
    credits: int
    price_tl: float
    is_active: bool = True

class CreditPackageUpdate(BaseModel):
    name: Optional[str] = None
    credits: Optional[int] = None
    price_tl: Optional[float] = None
    is_active: Optional[bool] = None

class CreditPackageResponse(BaseModel):
    id: int
    polar_product_id: str
    name: str
    credits: int
    price_tl: float
    is_active: bool
    created_at: datetime
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
    """Varsayılan token cost kayıtlarını oluştur/güncelle (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    default_costs = [
        {"endpoint": "/api/forecast/batch", "method": "POST", "cost": 5, "is_active": True},
        {"endpoint": "/api/forecast/batch/async", "method": "POST", "cost": 8, "is_active": True},
        {"endpoint": "/api/safety-stock", "method": "POST", "cost": 3, "is_active": True},
        {"endpoint": "/api/safety-stock/batch/async", "method": "POST", "cost": 6, "is_active": True},
        {"endpoint": "/api/simulate", "method": "POST", "cost": 10, "is_active": True},
        {"endpoint": "/api/simulate/batch/async", "method": "POST", "cost": 15, "is_active": True},
        {"endpoint": "/api/backtest", "method": "POST", "cost": 15, "is_active": True},
        {"endpoint": "/api/backtest/batch/async", "method": "POST", "cost": 20, "is_active": True},
        {"endpoint": "/api/supplier/optimize-shares", "method": "POST", "cost": 8, "is_active": True},
        {"endpoint": "/api/supplier/batch/async", "method": "POST", "cost": 12, "is_active": True},
        {"endpoint": "/api/tasks/async", "method": "GET", "cost": 0, "is_active": True},
    ]
    
    obsolete_endpoints = [
        "/api/pattern",
        "/api/forecast",
        "/api/risk/tail-risk",
        "/api/risk/cvar95",
        "/api/risk/service-level-gap",
    ]
    
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
    
    free_endpoints = [
        "/api/upload",
        "/api/upload/status",
        "/api/cost",
        "/api/dashboard/ai-summary",  # ✅ YENİ
        "/api/dashboard/ai-summary/status",  # ✅ YENİ
        "/api/dashboard/ai-summary/refresh",  # 
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
                record.is_active = False
                record.updated_at = datetime.utcnow()
            print(f"🆓 Ücretsiz: {endpoint}")
        else:
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
    }


# ============================================
# 🆕 CREDIT PACKAGE ENDPOINT'LERİ
# ============================================

@router.post("/credit-packages/init-defaults")
async def init_default_credit_packages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Varsayılan kredi paketlerini yükler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    default_packages = [
        {
            "polar_product_id": "prod_starter_xxx",
            "name": "Starter",
            "credits": 100,
            "price_tl": 1990,
            "is_active": True
        },
        {
            "polar_product_id": "prod_growth_yyy",
            "name": "Growth",
            "credits": 250,
            "price_tl": 4490,
            "is_active": True
        },
        {
            "polar_product_id": "prod_business_zzz",
            "name": "Business",
            "credits": 500,
            "price_tl": 7990,
            "is_active": True
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for package_data in default_packages:
        existing = db.query(CreditPackage).filter(
            CreditPackage.polar_product_id == package_data["polar_product_id"]
        ).first()
        
        if existing:
            existing.name = package_data["name"]
            existing.credits = package_data["credits"]
            existing.price_tl = package_data["price_tl"]
            existing.is_active = package_data["is_active"]
            existing.updated_at = datetime.utcnow()
            updated_count += 1
            print(f"🔄 Paket güncellendi: {package_data['name']}")
        else:
            new_package = CreditPackage(**package_data)
            db.add(new_package)
            created_count += 1
            print(f"✅ Paket eklendi: {package_data['name']}")
    
    db.commit()
    
    return {
        "message": "Default credit packages initialized",
        "created": created_count,
        "updated": updated_count,
        "total": len(default_packages),
        "packages": default_packages
    }


@router.get("/credit-packages", response_model=List[CreditPackageResponse])
async def get_credit_packages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm kredi paketlerini listeler (sadece admin)."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    packages = db.query(CreditPackage).order_by(CreditPackage.price_tl).all()
    return packages


@router.post("/credit-packages", response_model=CreditPackageResponse)
async def create_credit_package(
    package_data: CreditPackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni kredi paketi oluşturur (sadece admin)."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    existing = db.query(CreditPackage).filter(
        CreditPackage.polar_product_id == package_data.polar_product_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Package with product_id '{package_data.polar_product_id}' already exists"
        )
    
    new_package = CreditPackage(**package_data.dict())
    db.add(new_package)
    db.commit()
    db.refresh(new_package)
    
    return new_package


@router.put("/credit-packages/{package_id}", response_model=CreditPackageResponse)
async def update_credit_package(
    package_id: int,
    package_data: CreditPackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kredi paketini günceller (sadece admin)."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    package = db.query(CreditPackage).filter(CreditPackage.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    update_data = package_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(package, key, value)
    
    package.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(package)
    
    return package


@router.delete("/credit-packages/{package_id}")
async def delete_credit_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kredi paketini siler (sadece admin)."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    package = db.query(CreditPackage).filter(CreditPackage.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    db.delete(package)
    db.commit()
    
    return {"message": f"Package '{package.name}' deleted successfully"}


@router.get("/credit-transactions")
async def get_credit_transactions(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm kredi işlemlerini listeler (sadece admin)."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    total = db.query(CreditTransaction).count()
    
    transactions = db.query(CreditTransaction).order_by(
        CreditTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    result = []
    for t in transactions:
        user = db.query(User).filter(User.id == t.user_id).first()
        result.append({
            "id": t.id,
            "user_id": t.user_id,
            "amount": t.amount,
            "price": t.price,
            "transaction_type": t.transaction_type,
            "polar_order_id": t.polar_order_id,
            "polar_product_id": t.polar_product_id,
            "description": t.description,
            "created_at": t.created_at,
            "user": {
                "email": user.email if user else None,
                "full_name": user.full_name if user else None,
                "token_balance": user.token_balance if user else 0
            } if user else None
        })
    
    return {
        "total": total,
        "items": result
    }


@router.get("/credit-transactions/user/{user_id}")
async def get_user_credit_transactions(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Belirli bir kullanıcının kredi işlemlerini listeler (sadece admin)."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == user_id
    ).order_by(
        CreditTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return transactions


# ============================================
# 👥 KULLANICI BAZLI İSTATİSTİKLER
# ============================================

@router.get("/users/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı bazlı istatistikler (sadece admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    users = db.query(User).all()
    
    result = []
    for user in users:
        total_purchases = db.query(func.sum(CreditTransaction.amount)).filter(
            CreditTransaction.user_id == user.id,
            CreditTransaction.transaction_type == "purchase"
        ).scalar() or 0
        
        total_refunds = db.query(CreditTransaction).filter(
            CreditTransaction.user_id == user.id,
            CreditTransaction.transaction_type == "refund"
        ).count()
        
        total_refund_amount = db.query(func.sum(CreditTransaction.amount)).filter(
            CreditTransaction.user_id == user.id,
            CreditTransaction.transaction_type == "refund"
        ).scalar() or 0
        
        net_credits = total_purchases - abs(total_refund_amount)
        
        result.append({
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "total_purchases": total_purchases,
            "total_refunds": total_refunds,
            "net_credits": net_credits,
        })
    
    return result


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
    total_spent = sum(t.cost for t in today_tokens) if today_tokens else 0
    
    total_packages = db.query(CreditPackage).count()
    active_packages = db.query(CreditPackage).filter(CreditPackage.is_active == True).count()
    
    total_credit_transactions = db.query(CreditTransaction).filter(
        CreditTransaction.transaction_type == "purchase"  # ✅ Düzeltildi
    ).count()
    
    total_credits_sold = db.query(
        func.sum(CreditTransaction.amount)
    ).filter(
        CreditTransaction.transaction_type == "purchase"  # ✅ Düzeltildi
    ).scalar() or 0
    
    total_refunds = db.query(CreditTransaction).filter(
        CreditTransaction.transaction_type == "refund"  # ✅ Düzeltildi
    ).count()
    
    # ✅ Düzeltildi: status yerine transaction_type kullan
    total_revenue = db.query(
        func.sum(CreditTransaction.price)
    ).filter(
        CreditTransaction.transaction_type == "purchase"  # ✅ DÜZELTME
    ).scalar() or 0
    
    return {
        "users": {
            "total": total_users
        },
        "token_costs": {
            "total": total_token_costs,
            "active": active_token_costs
        },
        "token_usage": {
            "today_spent": total_spent,
            "today_transactions": len(today_tokens)
        },
        "credit_packages": {
            "total": total_packages,
            "active": active_packages
        },
        "credit_sales": {
            "total_transactions": total_credit_transactions,
            "total_credits_sold": total_credits_sold,
            "total_refunds": total_refunds,
            "total_revenue": total_revenue
        }
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