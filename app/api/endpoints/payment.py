from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import json
import os
import hmac
import hashlib
import re

router = APIRouter()

# Lemon Squeezy Webhook Secret (Lemon Squeezy dashboard'dan alınacak)
LEMON_SQUEEZY_SECRET = os.getenv("LEMON_SQUEEZY_SECRET", "your-webhook-secret")


@router.post("/webhook/lemon-squeezy")
async def lemon_squeezy_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.body()
        data = json.loads(body)
        
        if data.get("meta", {}).get("event_name") == "order_created":
            order_data = data.get("data", {}).get("attributes", {})
            user_email = order_data.get("user_email", "")
            product_name = order_data.get("first_order_item", {}).get("product_name", "")
            quantity = order_data.get("first_order_item", {}).get("quantity", 1)
            price = order_data.get("first_order_item", {}).get("price", 0)
            currency = order_data.get("first_order_item", {}).get("currency", "USD")
            payment_id = order_data.get("id", "")
            
            token_amount = _extract_token_amount(product_name) * quantity
            
            if token_amount > 0 and user_email:
                user = db.query(User).filter(User.email == user_email).first()
                if user:
                    # Token bakiyesini güncelle
                    user.token_balance += token_amount
                    
                    # Satın alma kaydı oluştur
                    purchase = TokenPurchase(
                        user_id=user.id,
                        amount=token_amount,
                        price=price,
                        currency=currency,
                        payment_id=payment_id,
                        status="completed"
                    )
                    db.add(purchase)
                    db.commit()
                    
                    return {"status": "success"}
        
        return {"status": "ignored"}
        
    except Exception as e:
        print(f"Webhook hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_token_amount(product_name: str) -> int:
    """Ürün adından token miktarını çıkar"""
    match = re.search(r'(\d+)\s*Token', product_name)
    if match:
        return int(match.group(1))
    return 0


@router.post("/payment/checkout")
async def create_checkout(request: Request):
    """
    Lemon Squeezy ödeme sayfası URL'si oluştur
    """
    try:
        body = await request.json()
        email = body.get("email")
        product_id = body.get("product_id")
        
        if not email or not product_id:
            raise HTTPException(status_code=400, detail="Email ve product_id gerekli")
        
        checkout_url = f"https://app.lemonsqueezy.com/checkout?product_id={product_id}&email={email}"
        
        return {"checkout_url": checkout_url}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment/plans")
def get_plans():
    """
    Token paketlerini getir
    """
    return {
        "plans": [
            {"id": "100-token", "name": "100 Token", "price": 10, "currency": "USD", "tokens": 100},
            {"id": "500-token", "name": "500 Token", "price": 40, "currency": "USD", "tokens": 500},
            {"id": "2000-token", "name": "2000 Token", "price": 150, "currency": "USD", "tokens": 2000},
            {"id": "10000-token", "name": "10000 Token", "price": 700, "currency": "USD", "tokens": 10000},
        ]
    }