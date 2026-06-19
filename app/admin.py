from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, TokenCost
from app.schemas import TokenCostCreate, TokenCostUpdate, TokenCostResponse, UserTokenUpdate
from app.auth import get_current_user
import os

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@stok.com")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918")  # "admin" in SHA256

router = APIRouter(tags=["admin"])

def is_admin(current_user: User = Depends(get_current_user)) -> bool:
    if current_user.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    return True

# ==================== KULLANICI YÖNETİMİ ====================
@router.get("/users")
def get_all_users(db: Session = Depends(get_db), _=Depends(is_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "token_balance": u.token_balance, "created_at": u.created_at} for u in users]

@router.post("/users/token")
def update_user_token(request: UserTokenUpdate, db: Session = Depends(get_db), _=Depends(is_admin)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    user.token_balance = request.token_balance
    db.commit()
    return {"msg": "Token bakiyesi güncellendi", "user_id": user.id, "new_balance": user.token_balance}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _=Depends(is_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    if user.email == ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Admin kullanıcı silinemez")
    db.delete(user)
    db.commit()
    return {"msg": f"Kullanıcı {user_id} silindi"}

# ==================== TOKEN MALİYET YÖNETİMİ ====================
@router.get("/token-costs", response_model=List[TokenCostResponse])
def get_all_token_costs(db: Session = Depends(get_db), _=Depends(is_admin)):
    return db.query(TokenCost).all()

@router.post("/token-costs")
def create_token_cost(request: TokenCostCreate, db: Session = Depends(get_db), _=Depends(is_admin)):
    existing = db.query(TokenCost).filter(TokenCost.endpoint == request.endpoint).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu endpoint zaten var")
    new_cost = TokenCost(**request.dict())
    db.add(new_cost)
    db.commit()
    db.refresh(new_cost)
    return new_cost

@router.put("/token-costs/{cost_id}")
def update_token_cost(cost_id: int, request: TokenCostUpdate, db: Session = Depends(get_db), _=Depends(is_admin)):
    cost = db.query(TokenCost).filter(TokenCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    if request.cost is not None:
        cost.cost = request.cost
    if request.is_active is not None:
        cost.is_active = request.is_active
    cost.updated_at = datetime.utcnow()
    db.commit()
    return cost

@router.delete("/token-costs/{cost_id}")
def delete_token_cost(cost_id: int, db: Session = Depends(get_db), _=Depends(is_admin)):
    cost = db.query(TokenCost).filter(TokenCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    db.delete(cost)
    db.commit()
    return {"msg": "Silindi"}

# ==================== VARSAYILAN TOKEN MALİYETLERİNİ YÜKLE ====================
@router.post("/token-costs/init-defaults")
def init_default_token_costs(db: Session = Depends(get_db), _=Depends(is_admin)):
    defaults = [
        {"endpoint": "/api/pattern", "method": "POST", "cost": 2},
        {"endpoint": "/api/safety-stock", "method": "POST", "cost": 3},
        {"endpoint": "/api/forecast", "method": "POST", "cost": 5},
        {"endpoint": "/api/simulate", "method": "POST", "cost": 10},
        {"endpoint": "/api/backtest", "method": "POST", "cost": 15},
        {"endpoint": "/api/upload", "method": "POST", "cost": 1},
        {"endpoint": "/api/supplier/optimize-shares", "method": "POST", "cost": 8},
        {"endpoint": "/api/risk/tail-risk", "method": "POST", "cost": 3},
        {"endpoint": "/api/risk/cvar95", "method": "POST", "cost": 2},
        {"endpoint": "/api/risk/service-level-gap", "method": "POST", "cost": 1},
    ]
    for d in defaults:
        existing = db.query(TokenCost).filter(TokenCost.endpoint == d["endpoint"]).first()
        if not existing:
            new_cost = TokenCost(**d)
            db.add(new_cost)
    db.commit()
    return {"msg": "Varsayılan token maliyetleri yüklendi", "count": len(defaults)}