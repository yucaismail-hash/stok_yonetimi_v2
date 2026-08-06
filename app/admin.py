from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel as PydanticBaseModel
from datetime import datetime
from app.database import get_db
from app.models import *
from app.auth import get_current_user


from app.auth import get_current_user, get_current_user_optional
from app.schemas.admin import (
    ValidationRuleCreate,
    ValidationRuleUpdate,
    AnalysisImpactRuleCreate,
    AnalysisImpactRuleUpdate,
    NormalizationRuleCreate,
    NormalizationRuleUpdate,
)
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

class TokenCostCreate(PydanticBaseModel):
    endpoint: str
    method: str = "POST"
    cost: int = 1
    is_active: bool = True

class TokenCostUpdate(PydanticBaseModel):
    cost: Optional[int] = None
    is_active: Optional[bool] = None

class TokenCostResponse(PydanticBaseModel):
    id: int
    endpoint: str
    method: str
    cost: int
    is_active: bool
    updated_at: datetime


# ============================================
# 🆕 CREDIT PACKAGE MODELLERİ
# ============================================

class CreditPackageCreate(PydanticBaseModel):
    polar_product_id: str
    name: str
    credits: int
    price_tl: float
    is_active: bool = True

class CreditPackageUpdate(PydanticBaseModel):
    name: Optional[str] = None
    credits: Optional[int] = None
    price_tl: Optional[float] = None
    is_active: Optional[bool] = None

class CreditPackageResponse(PydanticBaseModel):
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
        "/api/dashboard/ai-summary",
        "/api/dashboard/ai-summary/status",
        "/api/dashboard/ai-summary/refresh",
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
        CreditTransaction.transaction_type == "purchase"
    ).count()
    
    total_credits_sold = db.query(
        func.sum(CreditTransaction.amount)
    ).filter(
        CreditTransaction.transaction_type == "purchase"
    ).scalar() or 0
    
    total_refunds = db.query(CreditTransaction).filter(
        CreditTransaction.transaction_type == "refund"
    ).count()
    
    total_revenue = db.query(
        func.sum(CreditTransaction.price)
    ).filter(
        CreditTransaction.transaction_type == "purchase"
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


# ============================================================
# 🆕 PROCESSING CREDIT - ADMIN ENDPOINT'LERİ
# ============================================================

# ✅ DÜZELTİLDİ: AnalysisDataset yerine Dataset kullanıldı
from app.models import EndpointProfile, ProcessingScoreRange, Dataset, ProcessingTransaction
from app.schemas.credit import (
    EndpointProfileCreate,
    EndpointProfileUpdate,
    EndpointProfileResponse,
    ProcessingScoreRangeCreate,
    ProcessingScoreRangeUpdate,
    ProcessingScoreRangeResponse
)


# ----- ENDPOINT PROFİL ENDPOINT'LERİ -----

@router.get("/endpoint-profiles", response_model=List[EndpointProfileResponse])
async def get_endpoint_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm endpoint profillerini listeler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    profiles = db.query(EndpointProfile).order_by(EndpointProfile.endpoint).all()
    return profiles


@router.post("/endpoint-profiles", response_model=EndpointProfileResponse)
async def create_endpoint_profile(
    request: EndpointProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni endpoint profili oluşturur (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    existing = db.query(EndpointProfile).filter(
        EndpointProfile.endpoint == request.endpoint
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Bu endpoint zaten kayıtlı: {request.endpoint}"
        )
    
    profile = EndpointProfile(
        endpoint=request.endpoint,
        method=request.method,
        base_credit=request.base_credit,
        pricing_type=request.pricing_type,
        algorithm_weight=request.algorithm_weight,
        avg_time_per_unit=request.avg_time_per_unit,
        description=request.description,
        is_active=request.is_active,
        version="1.0"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


@router.put("/endpoint-profiles/{profile_id}", response_model=EndpointProfileResponse)
async def update_endpoint_profile(
    profile_id: int,
    request: EndpointProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint profilini günceller (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    profile = db.query(EndpointProfile).filter(EndpointProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil bulunamadı")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    
    return profile


@router.delete("/endpoint-profiles/{profile_id}")
async def delete_endpoint_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint profilini siler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    profile = db.query(EndpointProfile).filter(EndpointProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil bulunamadı")
    
    db.delete(profile)
    db.commit()
    
    return {"message": f"Profil silindi: {profile.endpoint}"}


@router.post("/endpoint-profiles/init-defaults")
async def init_default_endpoint_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Varsayılan endpoint profillerini yükler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    default_profiles = [
        {
            "endpoint": "/api/forecast/batch",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS",
            "algorithm_weight": 2.3,
            "description": "Talep tahmini analizi"
        },
        {
            "endpoint": "/api/forecast/batch/async",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS",
            "algorithm_weight": 2.3,
            "description": "Talep tahmini analizi (Async)"
        },
        {
            "endpoint": "/api/safety-stock/batch",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS",
            "algorithm_weight": 1.0,
            "description": "Emniyet stoğu analizi"
        },
        {
            "endpoint": "/api/safety-stock/batch/async",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS",
            "algorithm_weight": 1.0,
            "description": "Emniyet stoğu analizi (Async)"
        },
        {
            "endpoint": "/api/simulate/batch",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS_ITERATION",
            "algorithm_weight": 8.5,
            "description": "Monte Carlo simülasyonu"
        },
        {
            "endpoint": "/api/simulate/batch/async",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS_ITERATION",
            "algorithm_weight": 8.5,
            "description": "Monte Carlo simülasyonu (Async)"
        },
        {
            "endpoint": "/api/backtest/batch",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS_ITERATION",
            "algorithm_weight": 12.0,
            "description": "Backtest analizi"
        },
        {
            "endpoint": "/api/backtest/batch/async",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS_ITERATION",
            "algorithm_weight": 12.0,
            "description": "Backtest analizi (Async)"
        },
        {
            "endpoint": "/api/supplier/batch",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS",
            "algorithm_weight": 1.4,
            "description": "Tedarikçi analizi"
        },
        {
            "endpoint": "/api/supplier/batch/async",
            "method": "POST",
            "base_credit": 1,
            "pricing_type": "DATA_POINTS",
            "algorithm_weight": 1.4,
            "description": "Tedarikçi analizi (Async)"
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for data in default_profiles:
        existing = db.query(EndpointProfile).filter(
            EndpointProfile.endpoint == data["endpoint"]
        ).first()
        
        if existing:
            existing.base_credit = data["base_credit"]
            existing.pricing_type = data["pricing_type"]
            existing.algorithm_weight = data["algorithm_weight"]
            existing.description = data["description"]
            existing.updated_at = datetime.utcnow()
            updated_count += 1
        else:
            profile = EndpointProfile(**data, version="1.0", is_active=True)
            db.add(profile)
            created_count += 1
    
    db.commit()
    
    return {
        "message": "Varsayılan endpoint profilleri yüklendi",
        "created": created_count,
        "updated": updated_count,
        "total": len(default_profiles)
    }


# ----- PROCESSING SCORE RANGE ENDPOINT'LERİ -----

@router.get("/score-ranges", response_model=List[ProcessingScoreRangeResponse])
async def get_score_ranges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm Processing Score aralıklarını listeler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    ranges = db.query(ProcessingScoreRange).order_by(
        ProcessingScoreRange.min_score
    ).all()
    return ranges


@router.post("/score-ranges", response_model=ProcessingScoreRangeResponse)
async def create_score_range(
    request: ProcessingScoreRangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni Processing Score aralığı oluşturur (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    # Çakışma kontrolü
    existing = db.query(ProcessingScoreRange).filter(
        ProcessingScoreRange.min_score <= request.max_score,
        ProcessingScoreRange.max_score >= request.min_score
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Bu aralık çakışıyor: {existing.min_score}-{existing.max_score}"
        )
    
    range_record = ProcessingScoreRange(**request.dict())
    db.add(range_record)
    db.commit()
    db.refresh(range_record)
    
    return range_record


@router.put("/score-ranges/{range_id}", response_model=ProcessingScoreRangeResponse)
async def update_score_range(
    range_id: int,
    request: ProcessingScoreRangeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Processing Score aralığını günceller (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    range_record = db.query(ProcessingScoreRange).filter(
        ProcessingScoreRange.id == range_id
    ).first()
    
    if not range_record:
        raise HTTPException(status_code=404, detail="Aralık bulunamadı")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(range_record, key, value)
    
    range_record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(range_record)
    
    return range_record


@router.delete("/score-ranges/{range_id}")
async def delete_score_range(
    range_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Processing Score aralığını siler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    range_record = db.query(ProcessingScoreRange).filter(
        ProcessingScoreRange.id == range_id
    ).first()
    
    if not range_record:
        raise HTTPException(status_code=404, detail="Aralık bulunamadı")
    
    db.delete(range_record)
    db.commit()
    
    return {"message": f"Aralık silindi: {range_record.min_score}-{range_record.max_score}"}


@router.post("/score-ranges/init-defaults")
async def init_default_score_ranges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Varsayılan Processing Score aralıklarını yükler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    default_ranges = [
        {"min_score": 0, "max_score": 20000, "credit_cost": 3, "description": "Düşük işlem yükü"},
        {"min_score": 20001, "max_score": 50000, "credit_cost": 5, "description": "Orta-düşük işlem yükü"},
        {"min_score": 50001, "max_score": 100000, "credit_cost": 8, "description": "Orta işlem yükü"},
        {"min_score": 100001, "max_score": 250000, "credit_cost": 12, "description": "Orta-yüksek işlem yükü"},
        {"min_score": 250001, "max_score": 500000, "credit_cost": 18, "description": "Yüksek işlem yükü"},
        {"min_score": 500001, "max_score": 999999999, "credit_cost": 25, "description": "Çok yüksek işlem yükü"}
    ]
    
    created_count = 0
    updated_count = 0
    
    for data in default_ranges:
        existing = db.query(ProcessingScoreRange).filter(
            ProcessingScoreRange.min_score == data["min_score"],
            ProcessingScoreRange.max_score == data["max_score"]
        ).first()
        
        if existing:
            existing.credit_cost = data["credit_cost"]
            existing.description = data["description"]
            existing.updated_at = datetime.utcnow()
            updated_count += 1
        else:
            range_record = ProcessingScoreRange(**data, is_active=True)
            db.add(range_record)
            created_count += 1
    
    db.commit()
    
    return {
        "message": "Varsayılan Processing Score aralıkları yüklendi",
        "created": created_count,
        "updated": updated_count,
        "total": len(default_ranges)
    }


# ----- PROCESSING TRANSACTION ENDPOINT'LERİ -----

@router.get("/processing-transactions")
async def get_processing_transactions(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm işlem kredisi harcamalarını listeler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    total = db.query(ProcessingTransaction).count()
    
    transactions = db.query(ProcessingTransaction).order_by(
        ProcessingTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    result = []
    for t in transactions:
        user = db.query(User).filter(User.id == t.user_id).first()
        # ✅ DÜZELTİLDİ: AnalysisDataset yerine Dataset
        dataset = db.query(Dataset).filter(
            Dataset.id == t.dataset_id
        ).first() if t.dataset_id else None
        
        result.append({
            "id": t.id,
            "user_id": t.user_id,
            "user_email": user.email if user else None,
            "dataset_id": t.dataset_id,
            "endpoint": t.endpoint,
            "processing_score": t.processing_score,
            "credit_cost": t.credit_cost,
            "balance_after": t.balance_after,
            "elapsed_time_ms": t.elapsed_time_ms,
            "avg_time_per_unit_ms": t.avg_time_per_unit_ms,
            "status": t.status,
            "created_at": t.created_at,
            "dataset": {
                "sku_count": dataset.sku_count if dataset else 0,
                "record_count": dataset.record_count if dataset else 0,
            } if dataset else None
        })
    
    return {
        "total": total,
        "items": result
    }


@router.get("/processing-transactions/user/{user_id}")
async def get_user_processing_transactions(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Belirli bir kullanıcının işlem kredisi harcamalarını listeler (Admin)"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    transactions = db.query(ProcessingTransaction).filter(
        ProcessingTransaction.user_id == user_id
    ).order_by(
        ProcessingTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "total": len(transactions),
        "items": transactions
    }

# ============================================================
# 📌 MEVCUT ADMIN ENDPOINT'LER (KORUNUYOR)
# ============================================================

def require_admin(current_user: User = Depends(get_current_user)):
    """Admin yetkisi kontrolü"""
    if current_user.email not in ['admin@stok.com', 'admin@admin.com']:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    return current_user


@router.get("/credit-transactions")
async def get_credit_transactions(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Tüm kredi işlemlerini getir"""
    transactions = db.query(CreditTransaction).order_by(
        CreditTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    total = db.query(CreditTransaction).count()
    
    # Kullanıcı bilgilerini ekle
    result = []
    for t in transactions:
        user = db.query(User).filter(User.id == t.user_id).first()
        result.append({
            **t.__dict__,
            'user': {
                'email': user.email if user else None,
                'full_name': user.full_name if user else None,
                'token_balance': user.token_balance if user else 0
            }
        })
    
    return {
        'items': result,
        'total': total,
        'limit': limit,
        'offset': offset
    }


@router.get("/dashboard/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin dashboard istatistikleri"""
    total_users = db.query(User).count()
    total_transactions = db.query(CreditTransaction).count()
    
    purchases = db.query(CreditTransaction).filter(
        CreditTransaction.transaction_type == 'purchase'
    ).all()
    
    refunds = db.query(CreditTransaction).filter(
        CreditTransaction.transaction_type == 'refund'
    ).all()
    
    total_credits_sold = sum(t.amount for t in purchases) if purchases else 0
    total_refunds = len(refunds)
    total_revenue = sum(t.price for t in purchases if t.price) if purchases else 0
    
    return {
        'credit_sales': {
            'total_transactions': total_transactions,
            'total_credits_sold': total_credits_sold,
            'total_refunds': total_refunds,
            'total_revenue': total_revenue,
        },
        'users': {
            'total': total_users,
        }
    }


@router.get("/users/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Kullanıcı bazlı istatistikler"""
    users = db.query(User).all()
    result = []
    
    for user in users:
        purchases = db.query(CreditTransaction).filter(
            CreditTransaction.user_id == user.id,
            CreditTransaction.transaction_type == 'purchase'
        ).all()
        
        refunds = db.query(CreditTransaction).filter(
            CreditTransaction.user_id == user.id,
            CreditTransaction.transaction_type == 'refund'
        ).all()
        
        result.append({
            'user_id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'total_purchases': len(purchases),
            'total_refunds': len(refunds),
            'net_credits': sum(t.amount for t in purchases) - sum(t.amount for t in refunds) if purchases else 0,
        })
    
    return result


# ============================================================
# 🆕 VALIDATION RULES ENDPOINT'LERİ
# ============================================================

# ----- ValidationRule -----

@router.get("/validation-rules")
async def get_validation_rules(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Tüm validasyon kurallarını getir"""
    query = db.query(ValidationRule)
    if is_active is not None:
        query = query.filter(ValidationRule.is_active == is_active)
    return query.order_by(ValidationRule.created_at.desc()).all()


@router.post("/validation-rules")
async def create_validation_rule(
    rule: ValidationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Yeni validasyon kuralı oluştur"""
    new_rule = ValidationRule(**rule.dict())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.put("/validation-rules/{rule_id}")
async def update_validation_rule(
    rule_id: int,
    rule: ValidationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Validasyon kuralını güncelle"""
    db_rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    for key, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/validation-rules/{rule_id}")
async def delete_validation_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Validasyon kuralını sil"""
    db_rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    db.delete(db_rule)
    db.commit()
    return {"success": True}


@router.post("/validation-rules/init-defaults")
async def init_default_validation_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Varsayılan validasyon kurallarını oluştur"""
    defaults = [
        # Kolon kontrolleri
        {
            'rule_type': 'column_check',
            'table_name': 'Temel_Veriler',
            'column_name': 'Ürün Kodu',
            'rule_config': {'required': True},
            'severity': 'error',
            'description': 'Ürün Kodu kolonu zorunludur'
        },
        {
            'rule_type': 'column_check',
            'table_name': 'Temel_Veriler',
            'column_name': 'Ürün Adı',
            'rule_config': {'required': True},
            'severity': 'warning',
            'description': 'Ürün Adı kolonu önerilir'
        },
        {
            'rule_type': 'column_check',
            'table_name': 'Temel_Veriler',
            'column_name': 'Ürün Grubu',
            'rule_config': {'required': False},
            'severity': 'warning',
            'description': 'Ürün Grubu kolonu önerilir (AI öğrenmesi için)'
        },
        {
            'rule_type': 'column_check',
            'table_name': 'Temel_Veriler',
            'column_name': 'Tedarik Süresi (Gün)',
            'rule_config': {'required': True},
            'severity': 'error',
            'description': 'Tedarik Süresi kolonu zorunludur'
        },
        # Veri tipi kontrolleri
        {
            'rule_type': 'data_type',
            'table_name': 'Temel_Veriler',
            'column_name': 'Tedarik Süresi (Gün)',
            'rule_config': {'type': 'number', 'min': 0},
            'severity': 'error',
            'description': 'Tedarik Süresi pozitif sayı olmalıdır'
        },
        # İş kuralı kontrolleri
        {
            'rule_type': 'business_rule',
            'table_name': 'Temel_Veriler',
            'column_name': 'Birim Maliyet (TL)',
            'rule_config': {'min': 0},
            'severity': 'warning',
            'description': 'Birim Maliyet negatif olamaz'
        },
        {
            'rule_type': 'business_rule',
            'table_name': 'Temel_Veriler',
            'column_name': 'Stok Tutma Oranı (%)',
            'rule_config': {'min': 0, 'max': 100},
            'severity': 'warning',
            'description': 'Stok Tutma Oranı 0-100 arasında olmalıdır'
        },
    ]
    
    for rule_data in defaults:
        existing = db.query(ValidationRule).filter(
            ValidationRule.rule_type == rule_data['rule_type'],
            ValidationRule.table_name == rule_data['table_name'],
            ValidationRule.column_name == rule_data['column_name']
        ).first()
        
        if not existing:
            new_rule = ValidationRule(**rule_data)
            db.add(new_rule)
    
    db.commit()
    return {"success": True, "message": "Varsayılan kurallar oluşturuldu"}


# ============================================================
# 🆕 ANALYSIS IMPACT RULES ENDPOINT'LERİ
# ============================================================

@router.get("/analysis-impact-rules")
async def get_analysis_impact_rules(
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Tüm analiz etki kurallarını getir"""
    query = db.query(AnalysisImpactRule)
    if analysis_type:
        query = query.filter(AnalysisImpactRule.analysis_type == analysis_type)
    return query.order_by(AnalysisImpactRule.analysis_type).all()


@router.post("/analysis-impact-rules")
async def create_analysis_impact_rule(
    rule: AnalysisImpactRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Yeni analiz etki kuralı oluştur"""
    new_rule = AnalysisImpactRule(**rule.dict())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.put("/analysis-impact-rules/{rule_id}")
async def update_analysis_impact_rule(
    rule_id: int,
    rule: AnalysisImpactRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Analiz etki kuralını güncelle"""
    db_rule = db.query(AnalysisImpactRule).filter(AnalysisImpactRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    for key, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/analysis-impact-rules/{rule_id}")
async def delete_analysis_impact_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Analiz etki kuralını sil"""
    db_rule = db.query(AnalysisImpactRule).filter(AnalysisImpactRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    db.delete(db_rule)
    db.commit()
    return {"success": True}


@router.post("/analysis-impact-rules/init-defaults")
async def init_default_analysis_impact_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Varsayılan analiz etki kurallarını oluştur"""
    defaults = [
        # Forecast
        {'analysis_type': 'forecast', 'field_name': 'Ürün Kodu', 'importance': 'critical', 'min_weeks_required': 12},
        {'analysis_type': 'forecast', 'field_name': 'W1-Wn', 'importance': 'critical', 'min_weeks_required': 12},
        {'analysis_type': 'forecast', 'field_name': 'Ürün Grubu', 'importance': 'recommended', 'min_weeks_required': None},
        # Safety Stock
        {'analysis_type': 'safety_stock', 'field_name': 'Ürün Kodu', 'importance': 'critical', 'min_weeks_required': 8},
        {'analysis_type': 'safety_stock', 'field_name': 'W1-Wn', 'importance': 'critical', 'min_weeks_required': 8},
        {'analysis_type': 'safety_stock', 'field_name': 'Tedarik Süresi (Gün)', 'importance': 'critical', 'min_weeks_required': None},
        {'analysis_type': 'safety_stock', 'field_name': 'Dönem Başı Stok', 'importance': 'recommended', 'min_weeks_required': None},
        {'analysis_type': 'safety_stock', 'field_name': 'Birim Maliyet (TL)', 'importance': 'recommended', 'min_weeks_required': None},
        # Supplier
        {'analysis_type': 'supplier', 'field_name': 'Tedarikçi Kodu', 'importance': 'critical', 'min_weeks_required': None},
        {'analysis_type': 'supplier', 'field_name': 'Zamanında Teslim Oranı (%)', 'importance': 'critical', 'min_weeks_required': None},
        {'analysis_type': 'supplier', 'field_name': 'Ortalama Teslim Süresi (Gün)', 'importance': 'critical', 'min_weeks_required': None},
        # Simulation
        {'analysis_type': 'simulation', 'field_name': 'Ürün Kodu', 'importance': 'critical', 'min_weeks_required': 4},
        {'analysis_type': 'simulation', 'field_name': 'W1-Wn', 'importance': 'critical', 'min_weeks_required': 4},
        {'analysis_type': 'simulation', 'field_name': 'Tedarik Süresi (Gün)', 'importance': 'critical', 'min_weeks_required': None},
        {'analysis_type': 'simulation', 'field_name': 'Birim Maliyet (TL)', 'importance': 'recommended', 'min_weeks_required': None},
        # Backtest
        {'analysis_type': 'backtest', 'field_name': 'Ürün Kodu', 'importance': 'critical', 'min_weeks_required': 4},
        {'analysis_type': 'backtest', 'field_name': 'W1-Wn', 'importance': 'critical', 'min_weeks_required': 4},
    ]
    
    for rule_data in defaults:
        existing = db.query(AnalysisImpactRule).filter(
            AnalysisImpactRule.analysis_type == rule_data['analysis_type'],
            AnalysisImpactRule.field_name == rule_data['field_name']
        ).first()
        
        if not existing:
            new_rule = AnalysisImpactRule(**rule_data)
            db.add(new_rule)
    
    db.commit()
    return {"success": True, "message": "Varsayılan analiz etki kuralları oluşturuldu"}


# ============================================================
# 🆕 NORMALIZATION RULES ENDPOINT'LERİ
# ============================================================

@router.get("/normalization-rules")
async def get_normalization_rules(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Tüm normalizasyon kurallarını getir"""
    query = db.query(NormalizationRule)
    if is_active is not None:
        query = query.filter(NormalizationRule.is_active == is_active)
    return query.order_by(NormalizationRule.rule_name).all()


@router.post("/normalization-rules")
async def create_normalization_rule(
    rule: NormalizationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Yeni normalizasyon kuralı oluştur"""
    new_rule = NormalizationRule(**rule.dict())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.put("/normalization-rules/{rule_id}")
async def update_normalization_rule(
    rule_id: int,
    rule: NormalizationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Normalizasyon kuralını güncelle"""
    db_rule = db.query(NormalizationRule).filter(NormalizationRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    for key, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/normalization-rules/{rule_id}")
async def delete_normalization_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Normalizasyon kuralını sil"""
    db_rule = db.query(NormalizationRule).filter(NormalizationRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    
    db.delete(db_rule)
    db.commit()
    return {"success": True}


@router.post("/normalization-rules/init-defaults")
async def init_default_normalization_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Varsayılan normalizasyon kurallarını oluştur"""
    defaults = [
        {
            'rule_name': 'trim_whitespace',
            'pattern': r'^\s+|\s+$',
            'replacement': '',
            'confidence_threshold': 0.95,
            'description': 'Baştaki ve sondaki boşlukları temizle'
        },
        {
            'rule_name': 'collapse_spaces',
            'pattern': r'\s+',
            'replacement': ' ',
            'confidence_threshold': 0.95,
            'description': 'Çoklu boşlukları tek boşluğa çevir'
        },
        {
            'rule_name': 'remove_tabs',
            'pattern': r'\t',
            'replacement': ' ',
            'confidence_threshold': 0.95,
            'description': 'TAB karakterlerini boşluk ile değiştir'
        },
        {
            'rule_name': 'normalize_number_dot',
            'pattern': r'^(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)$',
            'replacement': None,
            'confidence_threshold': 0.9,
            'description': '10.000,00 → 10000 formatına çevir'
        },
        {
            'rule_name': 'normalize_number_comma',
            'pattern': r'^(\d+,\d{2})$',
            'replacement': None,
            'confidence_threshold': 0.9,
            'description': '10000,00 → 10000.00 formatına çevir'
        },
        {
            'rule_name': 'uppercase_code',
            'pattern': r'^([a-zA-Z0-9_-]+)$',
            'replacement': None,
            'confidence_threshold': 0.8,
            'description': 'Ürün kodlarını büyük harfe çevir'
        },
    ]
    
    for rule_data in defaults:
        existing = db.query(NormalizationRule).filter(
            NormalizationRule.rule_name == rule_data['rule_name']
        ).first()
        
        if not existing:
            new_rule = NormalizationRule(**rule_data)
            db.add(new_rule)
    
    db.commit()
    return {"success": True, "message": "Varsayılan normalizasyon kuralları oluşturuldu"}
