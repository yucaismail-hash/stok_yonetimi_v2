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
            # ✅ success_url ve cancel_url GÖNDERME
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
            "price": transaction.price,
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
            "price": purchase.price,
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
# 🆕 POLAR ORDER DETAYLARI
# ============================================

@router.get("/order/{order_id}")
async def get_polar_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Polar'dan order detaylarını getirir.
    Sadece admin kullanıcılar erişebilir.
    """
    admin_emails = ["admin@stok.com", "admin@admin.com"]
    if current_user.email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin yetkisi gerekli"
        )
    
    try:
        order = await polar_service.get_order(order_id)
        return order
    except Exception as e:
        print(f"❌ Order getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found: {order_id}"
        )


# ============================================
# 🆕 REFUND ENDPOINT'İ (Para + Kredi İadesi)
# ============================================

@router.post("/refund")
async def create_refund(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Polar üzerinden para iadesi (refund) oluşturur.
    Sadece admin kullanıcılar erişebilir.
    """
    # Admin kontrolü
    admin_emails = ["admin@stok.com", "admin@admin.com"]
    if current_user.email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin yetkisi gerekli"
        )
    
    # Request body'yi al
    data = await request.json()
    order_id = data.get("order_id")
    refund_credits = data.get("refund_credits")
    reason = data.get("reason", "customer_request")
    refund_type = data.get("refund_type", "money")  # Varsayılan 'money'
    
    # Validasyon
    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order_id gerekli"
        )
    
    # 1. Siparişi bul (CreditTransaction)
    transaction = db.query(CreditTransaction).filter(
        CreditTransaction.polar_order_id == order_id,
        CreditTransaction.transaction_type == "purchase"
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sipariş bulunamadı"
        )
    
    # 2. Kullanıcıyı bul
    user = db.query(User).filter(User.id == transaction.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # 3. İade miktarını belirle
    credits_to_refund = refund_credits if refund_credits else transaction.amount
    
    # 4. PARA İADESİ (Polar Refund)
    polar_refund_result = None
    try:
        # Order detaylarını al
        order = await polar_service.get_order(order_id)
        
        # ✅ Doğru iade miktarını al (refundable_amount veya net_amount)
        total_amount = order.get("refundable_amount")
        if not total_amount:
            total_amount = order.get("net_amount", 0)
        
        # ✅ Eğer amount 0 veya None ise hata ver
        if not total_amount or total_amount <= 0:
            raise Exception("İade edilebilir miktar bulunamadı")
        
        print(f"💰 İade edilebilir miktar: {total_amount} kuruş")
        
        # Polar refund oluştur
        polar_refund_result = await polar_service.create_refund(
            order_id=order_id,
            amount=total_amount,
            reason=reason
        )
        print(f"✅ Polar refund created: {polar_refund_result}")
    except Exception as e:
        print(f"❌ Polar refund hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Para iadesi başarısız: {str(e)}"
        )
    
    # 5. KREDİ İADESİ
    user.token_balance -= credits_to_refund
    
    # 6. İade kaydı oluştur
    price_to_refund = transaction.price if transaction.price else 0
    refund_transaction = CreditTransaction(
        user_id=user.id,
        amount=-credits_to_refund,
        price=-price_to_refund if refund_type == "money" else 0,
        transaction_type="refund",
        polar_order_id=order_id,
        polar_product_id=transaction.polar_product_id,
        description=f"İade - {reason} (Kredi: {credits_to_refund})" + (f" - Para iadesi: {polar_refund_result.get('id') if polar_refund_result else 'Yok'}" if refund_type == "money" else "")
    )
    db.add(refund_transaction)
    
    # 7. TokenPurchase durumunu güncelle
    purchase = db.query(TokenPurchase).filter(
        TokenPurchase.payment_id == order_id
    ).first()
    if purchase:
        purchase.status = "refunded"
    
    db.commit()
    
    return {
        "success": True,
        "refund_id": refund_transaction.id,
        "user_id": user.id,
        "user_email": user.email,
        "refund_amount": credits_to_refund,
        "refund_price": price_to_refund if refund_type == "money" else 0,
        "refund_amount_kurus": total_amount,
        "new_balance": user.token_balance,
        "reason": reason,
        "refund_type": refund_type,
        "polar_refund": polar_refund_result
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
    
    # ✅ İMZA DOĞRULAMAYI AÇ
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
    amount = order_data.get("amount")  # Kuruş cinsinden
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
        # 1. Paketi bul
        package = db.query(CreditPackage).filter(
            CreditPackage.polar_product_id == product_id,
            CreditPackage.is_active == True
        ).first()
        
        if not package:
            print(f"Unknown product ID: {product_id}")
            return
        
        print(f"✅ Package found: {package.name} ({package.credits} credits)")
        
        # 2. Kullanıcıyı bul
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
        
        # 3. Aynı sipariş kontrolü
        existing_transaction = db.query(CreditTransaction).filter(
            CreditTransaction.polar_order_id == order_id
        ).first()
        
        if existing_transaction:
            print(f"⚠️ Order {order_id} already processed")
            return
        
        # 4. Para miktarını al (kuruştan TL'ye çevir)
        price_tl = amount / 100 if amount else package.price_tl
        
        # 5. Kredi ekle
        user.token_balance += package.credits
        print(f"💰 New balance: {user.token_balance}")
        
        # ✅ CreditTransaction kaydı - price alanı ile birlikte
        try:
            transaction = CreditTransaction(
                user_id=user.id,
                amount=package.credits,
                price=price_tl,  # ✅ price alanı
                transaction_type="purchase",
                polar_order_id=order_id,
                polar_product_id=product_id,
                description=f"{package.name} paketi satın alındı ({package.credits} kredi) - {price_tl} TL"
            )
            db.add(transaction)
            print(f"✅ CreditTransaction added")
        except Exception as e:
            print(f"❌ CreditTransaction hatası: {e}")
            # Eğer price alanı yoksa, price'siz dene
            transaction = CreditTransaction(
                user_id=user.id,
                amount=package.credits,
                transaction_type="purchase",
                polar_order_id=order_id,
                polar_product_id=product_id,
                description=f"{package.name} paketi satın alındı ({package.credits} kredi)"
            )
            db.add(transaction)
            print(f"✅ CreditTransaction added (without price)")
        
        # 6. TokenPurchase kaydı
        purchase = TokenPurchase(
            user_id=user.id,
            amount=package.credits,
            price=price_tl,
            currency=currency,
            payment_id=order_id,
            status="completed"
        )
        db.add(purchase)
        print(f"✅ TokenPurchase added")
        
        # 7. UserTokenTransaction kaydı
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
        
        # 8. Bildirim ekle
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
        import traceback
        traceback.print_exc()
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
            price=-transaction.price if transaction.price else 0,
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