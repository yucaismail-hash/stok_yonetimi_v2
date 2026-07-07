from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, TokenHistory, UserTokenTransaction, Sector
from app.auth import get_current_user, get_password_hash, verify_password
import re

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


@router.get("/")
async def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı profil bilgilerini getir"""
    # ✅ Sektör adını al
    sector_name = None
    if current_user.sector_id:
        sector = db.query(Sector).filter(Sector.id == current_user.sector_id).first()
        sector_name = sector.name if sector else None
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "sector_id": current_user.sector_id,
        "sector_name": sector_name,  # ✅ Eklendi
        "token_balance": current_user.token_balance,
        "created_at": current_user.created_at
    }


@router.put("/")
async def update_profile(
    profile: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı profilini güncelle"""
    if profile.full_name is not None:
        current_user.full_name = profile.full_name
    if profile.company_name is not None:
        current_user.company_name = profile.company_name
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "message": "Profil güncellendi",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "company_name": current_user.company_name,
            "token_balance": current_user.token_balance
        }
    }


@router.post("/change-password")
async def change_password(
    request: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı şifresini değiştir"""
    # ✅ Mevcut şifre kontrolü
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre yanlış")
    
    # ✅ Yeni şifre kontrolü
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")
    
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Şifreler eşleşmiyor")
    
    # ✅ Şifreyi güncelle
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    return {"success": True, "message": "Şifre başarıyla değiştirildi"}


@router.get("/token-history")
async def get_token_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    transaction_type: Optional[str] = None
):
    """Token harcama geçmişini getir - SADECE cost > 0"""
    query = db.query(TokenHistory).filter(
        TokenHistory.user_id == current_user.id,
        TokenHistory.cost > 0  # ✅ 0 token'li işlemleri filtrele
    )
    
    if transaction_type == 'spend':
        query = query.filter(TokenHistory.cost > 0)
    
    total = query.count()
    history = query.order_by(TokenHistory.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "history": [
            {
                "id": h.id,
                "endpoint": h.endpoint,
                "cost": h.cost,
                "balance_after": h.balance_after,
                "created_at": h.created_at,
                "type": "spend"
            }
            for h in history
        ]
    }


@router.get("/transactions")
async def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    transaction_type: Optional[str] = None
):
    """Token işlem geçmişini getir (satın alma + harcama)"""
    query = db.query(UserTokenTransaction).filter(
        UserTokenTransaction.user_id == current_user.id,
        UserTokenTransaction.amount != 0  # ✅ Sıfır işlemleri filtrele
    )
    
    if transaction_type:
        query = query.filter(UserTokenTransaction.type == transaction_type)
    
    total = query.count()
    transactions = query.order_by(UserTokenTransaction.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "balance_after": t.balance_after,
                "created_at": t.created_at
            }
            for t in transactions
        ]
    }