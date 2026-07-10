from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models import User, UserTokenTransaction
from app.auth import get_current_user
import uuid

router = APIRouter(prefix="/payment", tags=["payment"])


class PurchaseRequest(BaseModel):
    amount: int  # Satın alınacak kredi miktarı
    payment_method: str = "credit_card"  # credit_card, bank_transfer, crypto


class PurchaseResponse(BaseModel):
    success: bool
    message: str
    transaction_id: Optional[str] = None
    new_balance: Optional[int] = None
    amount: Optional[int] = None


# 📦 Kredi Paketleri
KREDI_PAKETLERI = [
    {"amount": 50, "price": 49.99, "bonus": 0, "label": "Başlangıç"},
    {"amount": 100, "price": 89.99, "bonus": 10, "label": "Standart"},
    {"amount": 250, "price": 199.99, "bonus": 30, "label": "Profesyonel"},
    {"amount": 500, "price": 349.99, "bonus": 75, "label": "Kurumsal"},
    {"amount": 1000, "price": 599.99, "bonus": 200, "label": "Premium"},
]


@router.get("/packages")
async def get_packages():
    """Kredi paketlerini getir"""
    return {
        "success": True,
        "packages": KREDI_PAKETLERI
    }


@router.post("/purchase")
async def purchase_credits(
    request: PurchaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kredi satın al"""
    try:
        # Paketi bul
        package = None
        for p in KREDI_PAKETLERI:
            if p["amount"] == request.amount:
                package = p
                break
        
        if not package:
            raise HTTPException(status_code=400, detail="Geçersiz paket seçimi")
        
        # Benzersiz işlem ID
        transaction_id = str(uuid.uuid4())[:8].upper()
        
        # Toplam kredi (paket + bonus)
        total_credits = package["amount"] + package["bonus"]
        
        # Kullanıcı bakiyesini güncelle
        current_user.token_balance += total_credits
        
        # İşlem kaydı
        transaction = UserTokenTransaction(
            user_id=current_user.id,
            amount=total_credits,
            type="purchase",
            description=f"Kredi Satın Alma - {package['label']} ({package['amount']} + {package['bonus']} bonus)",
            balance_after=current_user.token_balance,
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        db.refresh(current_user)
        
        return {
            "success": True,
            "message": f"✅ {total_credits} kredi başarıyla satın alındı!",
            "transaction_id": transaction_id,
            "new_balance": current_user.token_balance,
            "amount": total_credits,
            "package": package
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Kredi satın alma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_purchase_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """Kullanıcının kredi satın alma geçmişi"""
    query = db.query(UserTokenTransaction).filter(
        UserTokenTransaction.user_id == current_user.id,
        UserTokenTransaction.type == "purchase"
    )
    
    total = query.count()
    history = query.order_by(UserTokenTransaction.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "history": [
            {
                "id": t.id,
                "amount": t.amount,
                "description": t.description,
                "balance_after": t.balance_after,
                "created_at": t.created_at
            }
            for t in history
        ]
    }