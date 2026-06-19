from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models import User, TokenHistory, TokenPurchase
from app.auth import get_current_user, get_password_hash, verify_password

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    full_name: str
    company_name: str
    sector_id: Optional[int] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sector_name = current_user.sector.name if current_user.sector else None
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name or "",
        "company_name": current_user.company_name or "",
        "sector_id": current_user.sector_id,
        "sector_name": sector_name,
        "token_balance": current_user.token_balance,
        "created_at": current_user.created_at.isoformat()
    }


@router.put("")
def update_profile(
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.full_name = request.full_name
    current_user.company_name = request.company_name
    current_user.sector_id = request.sector_id
    db.commit()
    db.refresh(current_user)
    sector_name = current_user.sector.name if current_user.sector else None
    return {
        "message": "Profil başarıyla güncellendi",
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "sector_id": current_user.sector_id,
        "sector_name": sector_name,
        "token_balance": current_user.token_balance
    }


@router.put("/password")
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre yanlış")
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Şifre başarıyla değiştirildi"}


@router.get("/token-history")
def get_token_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(TokenHistory).filter(
        TokenHistory.user_id == current_user.id
    ).order_by(TokenHistory.created_at.desc()).limit(50).all()
    
    if not history:
        return []
    
    return [
        {
            "id": h.id,
            "date": h.created_at.strftime("%Y-%m-%d %H:%M"),
            "endpoint": h.endpoint,
            "cost": h.cost,
            "balance_after": h.balance_after
        }
        for h in history
    ]


@router.get("/purchase-history")
def get_purchase_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchases = db.query(TokenPurchase).filter(
        TokenPurchase.user_id == current_user.id
    ).order_by(TokenPurchase.created_at.desc()).limit(20).all()
    
    if not purchases:
        return []
    
    return [
        {
            "id": p.id,
            "date": p.created_at.strftime("%Y-%m-%d %H:%M"),
            "amount": p.amount,
            "price": p.price,
            "currency": p.currency,
            "status": p.status
        }
        for p in purchases
    ]