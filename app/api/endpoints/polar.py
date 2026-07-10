"""
Polar.sh entegrasyonu - Checkout ve Webhook endpoint'leri
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional
import os
import json
from datetime import datetime

from app.database import get_db
from app.models import User, CreditPackage, CreditTransaction, TokenPurchase, UserTokenTransaction, Notification
from app.schemas import CheckoutRequest, CheckoutResponse
from app.services import polar as polar_service
from app.auth import get_current_user

router = APIRouter(prefix="/polar", tags=["polar"])

# Environment
POLAR_WEBHOOK_SECRET = os.getenv("POLAR_WEBHOOK_SECRET")
if not POLAR_WEBHOOK_SECRET:
    raise ValueError("POLAR_WEBHOOK_SECRET environment variable is required")


# ============================================
# CHECKOUT ENDPOINT'LERİ
# ============================================

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Polar checkout linki oluşturur.
    """
    print("=" * 60)
    print("🔍 [DEBUG] /checkout ENDPOINT BAŞLADI")
    print(f"   - User: {current_user.email}")
    print(f"   - Product ID: {request.product_id}")
    print("=" * 60)
    
    # 1. Paketi bul
    package = db.query(CreditPackage).filter(
        CreditPackage.polar_product_id == request.product_id,
        CreditPackage.is_active == True
    ).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found: {request.product_id}"
        )
    
    print(f"✅ Package found: {package.name} ({package.credits} credits)")
    
    # 2. Müşteri oluştur veya getir
    try:
        customer = await polar_service.create_or_get_customer(
            email=current_user.email,
            name=current_user.full_name or current_user.email
        )
        
        print(f"✅ Customer: {customer.get('id')}")
        
        if not current_user.polar_customer_id:
            current_user.polar_customer_id = customer.get("id")
            db.commit()
            print(f"✅ polar_customer_id saved: {current_user.polar_customer_id}")
        
    except Exception as e:
        print(f"❌ Customer error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Polar customer: {str(e)}"
        )
    
    # 3. Checkout oluştur
    try:
        embed_origin = os.getenv("EMBED_ORIGIN", "http://localhost:5173")
        
        checkout = await polar_service.create_checkout(
            product_id=request.product_id,
            customer_email=current_user.email,
            customer_name=current_user.full_name or current_user.email,
            customer_id=current_user.polar_customer_id,
            success_url=os.getenv("POLAR_SUCCESS_URL", "https://yourdomain.com/success"),
            cancel_url=os.getenv("POLAR_CANCEL_URL", "https://yourdomain.com/cancel"),
            embed_origin=embed_origin
        )
        
        print(f"✅ Checkout created: {checkout.get('url')}")
        print("=" * 60)
        
        return CheckoutResponse(
            checkout_url=checkout.get("url"),
            product_id=request.product_id,
            product_name=package.name
        )
        
    except Exception as e:
        print(f"❌ Checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout: {str(e)}"
        )


@router.get("/packages")
async def get_packages(db: Session = Depends(get_db)):
    """
    Tüm aktif kredi paketlerini listeler.
    """
    packages = db.query(CreditPackage).filter(
        CreditPackage.is_active == True
    ).all()
    
    return [
        {
            "id": p.id,
            "polar_product_id": p.polar_product_id,
            "name": p.name,
            "credits": p.credits,
            "price_tl": p.price_tl
        }
        for p in packages
    ]


@router.get("/transaction/{checkout_id}")
async def get_transaction(
    checkout_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Belirli bir checkout işleminin detaylarını getirir.
    """
    print("=" * 60)
    print("🔍 [DEBUG] /transaction/{checkout_id} BAŞLADI")
    print(f"   - checkout_id: {checkout_id}")
    print(f"   - User: {current_user.email}")
    print("=" * 60)
    
    # CreditTransaction tablosunda ara
    transaction = db.query(CreditTransaction).filter(
        CreditTransaction.polar_order_id == checkout_id,
        CreditTransaction.user_id == current_user.id
    ).first()
    
    if transaction:
        print(f"✅ [DEBUG] Found in CreditTransaction: {transaction}")
        return {
            "checkout_id": checkout_id,
            "credits": transaction.amount,
            "package_name": transaction.description,
            "status": "completed",
            "created_at": transaction.created_at
        }
    
    # TokenPurchase tablosunda ara
    purchase = db.query(TokenPurchase).filter(
        TokenPurchase.payment_id == checkout_id,
        TokenPurchase.user_id == current_user.id
    ).first()
    
    if purchase:
        print(f"✅ [DEBUG] Found in TokenPurchase: {purchase}")
        return {
            "checkout_id": checkout_id,
            "credits": purchase.amount,
            "package_name": "Kredi Satın Alma",
            "status": purchase.status,
            "created_at": purchase.created_at
        }
    
    print("❌ [DEBUG] Transaction not found")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Transaction not found"
    )


# ============================================
# 🆕 SUCCESS / CANCEL ENDPOINT'LERİ
# ============================================

@router.get("/success")
async def polar_success(
    checkout_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Polar başarılı ödeme sonrası dönecek endpoint.
    """
    transaction = db.query(CreditTransaction).filter(
        CreditTransaction.polar_order_id == checkout_id,
        CreditTransaction.user_id == current_user.id
    ).first()
    
    if transaction:
        return {
            "status": "success",
            "message": f"{transaction.amount} kredi hesabınıza eklendi!",
            "credits": transaction.amount
        }
    
    purchase = db.query(TokenPurchase).filter(
        TokenPurchase.payment_id == checkout_id,
        TokenPurchase.user_id == current_user.id
    ).first()
    
    if purchase:
        return {
            "status": "success",
            "message": f"{purchase.amount} kredi hesabınıza eklendi!",
            "credits": purchase.amount
        }
    
    return {
        "status": "success",
        "message": "Ödeme başarıyla tamamlandı!"
    }


@router.get("/cancel")
async def polar_cancel(
    checkout_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Polar iptal ödeme sonrası dönecek endpoint.
    """
    return {
        "status": "canceled",
        "message": "Ödeme işleminiz iptal edildi."
    }


# ============================================
# WEBHOOK ENDPOINT'İ
# ============================================

@router.post("/webhook")
async def polar_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Polar webhook endpoint'i.
    """
    payload = await request.body()
    
    webhook_id = request.headers.get("webhook-id")
    webhook_timestamp = request.headers.get("webhook-timestamp")
    webhook_signature = request.headers.get("webhook-signature")
    
    print(f"🔍 Webhook Headers:")
    print(f"  webhook-id: {webhook_id}")
    print(f"  webhook-timestamp: {webhook_timestamp}")
    print(f"  webhook-signature: {webhook_signature}")
    
    if not all([webhook_id, webhook_timestamp, webhook_signature]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook headers"
        )
    
    if not polar_service.verify_webhook_signature(
        payload, webhook_id, webhook_timestamp, webhook_signature
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature"
        )
    
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    event_type = data.get("type")
    event_data = data.get("data", {})
    
    print(f"🔍 Event type: {event_type}")
    
    if event_type in ["order.created", "order.paid"]:
        await handle_order_paid(event_data, db)
    elif event_type == "order.refunded":
        await handle_order_refunded(event_data, db)
    else:
        print(f"Unhandled webhook event: {event_type}")
    
    return {"status": "accepted"}


async def handle_order_paid(order_data: dict, db: Session):
    """
    Ödeme başarılı olduğunda kullanıcıya kredi ekle.
    """
    product_id = order_data.get("product_id")
    customer_id = order_data.get("customer_id")
    order_id = order_data.get("id")
    amount = order_data.get("amount")
    currency = order_data.get("currency", "USD")
    status = order_data.get("status")
    
    print(f"🔍 Webhook order_paid:")
    print(f"  product_id: {product_id}")
    print(f"  customer_id: {customer_id}")
    print(f"  order_id: {order_id}")
    print(f"  status: {status}")
    
    if not product_id or not customer_id:
        print("Missing product_id or customer_id")
        return
    
    if status != "paid":
        print(f"Order status is {status}, skipping")
        return
    
    try:
        package = db.query(CreditPackage).filter(
            CreditPackage.polar_product_id == product_id,
            CreditPackage.is_active == True
        ).first()
        
        if not package:
            print(f"Unknown product ID: {product_id}")
            return
        
        print(f"✅ Package found: {package.name} ({package.credits} credits)")
        
        user = db.query(User).filter(
            User.polar_customer_id == customer_id
        ).first()
        
        if not user:
            print(f"User not found with customer_id: {customer_id}")
            customer_email = order_data.get("customer", {}).get("email")
            if customer_email:
                print(f"🔍 Trying email: {customer_email}")
                user = db.query(User).filter(User.email == customer_email).first()
                if user:
                    user.polar_customer_id = customer_id
                    db.commit()
                    print(f"✅ Updated user {user.id} with customer_id: {customer_id}")
        
        if not user:
            print(f"❌ User not found for customer: {customer_id}")
            return
        
        print(f"✅ User found: {user.id} ({user.email})")
        print(f"💰 Current balance: {user.token_balance}")
        
        existing_transaction = db.query(CreditTransaction).filter(
            CreditTransaction.polar_order_id == order_id
        ).first()
        
        if existing_transaction:
            print(f"⚠️ Order {order_id} already processed")
            return
        
        user.token_balance += package.credits
        print(f"💰 New balance: {user.token_balance}")
        
        transaction = CreditTransaction(
            user_id=user.id,
            amount=package.credits,
            transaction_type="purchase",
            polar_order_id=order_id,
            polar_product_id=product_id,
            description=f"{package.name} paketi satın alındı ({package.credits} kredi) - {amount} {currency}"
        )
        db.add(transaction)
        print(f"✅ CreditTransaction added")
        
        purchase = TokenPurchase(
            user_id=user.id,
            amount=package.credits,
            price=amount / 100,
            currency=currency,
            payment_id=order_id,
            status="completed"
        )
        db.add(purchase)
        print(f"✅ TokenPurchase added")
        
        token_tx = UserTokenTransaction(
            user_id=user.id,
            amount=package.credits,
            type="purchase",
            description=f"{package.name} paketi satın alındı",
            endpoint="/api/polar/webhook",
            balance_after=user.token_balance
        )
        db.add(token_tx)
        print(f"✅ UserTokenTransaction added")
        
        try:
            notification = Notification(
                user_id=user.id,
                title="✅ Ödeme Başarılı!",
                message=f"{package.credits} kredi hesabınıza eklendi.",
                type="success",
                link="/dashboard"
            )
            db.add(notification)
            print(f"✅ Bildirim eklendi: User {user.id}")
        except Exception as e:
            print(f"❌ Bildirim hatası: {e}")
        
        db.commit()
        print(f"🎉 {package.credits} credits added to user {user.id} (Order: {order_id})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error processing order: {e}")
        raise


async def handle_order_refunded(order_data: dict, db: Session):
    """
    İade durumunda kredileri geri al.
    """
    product_id = order_data.get("product_id")
    customer_id = order_data.get("customer_id")
    order_id = order_data.get("id")
    
    try:
        user = db.query(User).filter(
            User.polar_customer_id == customer_id
        ).first()
        
        if not user:
            print(f"User not found for customer: {customer_id}")
            return
        
        transaction = db.query(CreditTransaction).filter(
            CreditTransaction.polar_order_id == order_id,
            CreditTransaction.transaction_type == "purchase"
        ).first()
        
        if not transaction:
            print(f"No purchase transaction found for order: {order_id}")
            return
        
        user.token_balance -= transaction.amount
        
        refund_tx = CreditTransaction(
            user_id=user.id,
            amount=-transaction.amount,
            transaction_type="refund",
            polar_order_id=order_id,
            polar_product_id=product_id,
            description=f"İade - {transaction.description}"
        )
        db.add(refund_tx)
        
        purchase = db.query(TokenPurchase).filter(
            TokenPurchase.payment_id == order_id
        ).first()
        if purchase:
            purchase.status = "refunded"
        
        db.commit()
        print(f"✅ Refund processed for order {order_id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error processing refund: {e}")
        raise