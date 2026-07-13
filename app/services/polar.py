"""
Polar.sh entegrasyon servisi - httpx ile (KESİN ÇÖZÜM)
"""
import os
import json
import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

POLAR_ACCESS_TOKEN = os.getenv("POLAR_ACCESS_TOKEN")
POLAR_WEBHOOK_SECRET = os.getenv("POLAR_WEBHOOK_SECRET")
POLAR_API_BASE = os.getenv("POLAR_API_BASE", "https://sandbox-api.polar.sh/v1")

if not POLAR_ACCESS_TOKEN:
    raise ValueError("POLAR_ACCESS_TOKEN environment variable is required")


async def create_or_get_customer(email: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    Polar'da müşteri oluşturur veya var olanı getirir.
    """
    # ✅ follow_redirects=True eklendi
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # 1. Müşteri ara
        logger.info(f"🔍 Searching customer: {email}")
        response = await client.get(
            f"{POLAR_API_BASE}/customers",
            headers={"Authorization": f"Bearer {POLAR_ACCESS_TOKEN}"},
            params={"email": email}
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items:
                customer = items[0]
                logger.info(f"✅ Existing customer found: {customer.get('id')}")
                return {
                    "id": customer.get("id"),
                    "email": customer.get("email"),
                    "name": customer.get("name")
                }
        
        # 2. Müşteri oluştur
        logger.info(f"📤 Creating customer: {email}")
        payload = {"email": email}
        if name:
            payload["name"] = name
        
        response = await client.post(
            f"{POLAR_API_BASE}/customers",
            headers={
                "Authorization": f"Bearer {POLAR_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            error_msg = f"Polar API error: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        customer = response.json()
        logger.info(f"✅ Customer created: {customer.get('id')}")
        return {
            "id": customer.get("id"),
            "email": customer.get("email"),
            "name": customer.get("name")
        }


async def create_checkout(
    product_id: str,
    customer_email: str,
    customer_name: Optional[str] = None,
    customer_id: Optional[str] = None,
    embed_origin: Optional[str] = None,
    billing_address: Optional[Dict[str, str]] = None,  # 🆕 Fatura adresi
    custom_field_data: Optional[Dict[str, str]] = None,  # 🆕 Custom field'lar
    require_billing_address: bool = False  # 🆕 Adres zorunlu mu?
) -> Dict[str, Any]:
    """
    Polar'da checkout link'i oluşturur.
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        if not customer_id:
            customer = await create_or_get_customer(customer_email, customer_name)
            customer_id = customer.get("id")
        
        logger.info(f"📤 Creating checkout for product: {product_id}")
        
        payload = {
            "product_id": product_id,
            "customer_id": customer_id,
        }
        
        # ✅ Fatura adresi ekle
        if billing_address:
            payload["customer_billing_address"] = billing_address
            logger.info(f"📍 Billing address: {billing_address}")
        
        # ✅ Custom field'ları ekle (vergi no, vergi dairesi, kimlik no)
        if custom_field_data:
            payload["custom_field_data"] = custom_field_data
            logger.info(f"📋 Custom fields: {custom_field_data}")
        
        # ✅ Adres zorunlu mu?
        if require_billing_address:
            payload["require_billing_address"] = True
        
        if embed_origin:
            payload["embed_origin"] = embed_origin
            logger.info(f"🔍 embed_origin: {embed_origin}")
        
        logger.info(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        response = await client.post(
            f"{POLAR_API_BASE}/checkouts",
            headers={
                "Authorization": f"Bearer {POLAR_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            error_msg = f"Polar API error: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        result = response.json()
        logger.info(f"✅ Checkout created: {result.get('url')}")
        return {
            "id": result.get("id"),
            "url": result.get("url"),
            "product_id": product_id,
        }
    
# app/services/polar.py

async def create_refund(
    order_id: str,
    amount: Optional[float] = None,
    reason: str = "customer_request"  # ✅ Varsayılan değeri değiştir
) -> Dict[str, Any]:
    """
    Polar üzerinden iade (refund) oluşturur.
    reason: duplicate, fraudulent, customer_request, service_disruption, satisfaction_guarantee, other
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # ✅ reason'ı Polar'ın beklediği formata dönüştür
        valid_reasons = [
            "duplicate", "fraudulent", "customer_request", 
            "service_disruption", "satisfaction_guarantee", "other"
        ]
        
        # Eğer gönderilen reason geçerli değilse "other" kullan
        if reason not in valid_reasons:
            reason = "other"
            logger.warning(f"⚠️ Geçersiz reason, 'other' olarak değiştirildi")
        
        payload = {
            "order_id": order_id,
            "reason": reason,  # ✅ Sabit değer
        }
        
        if amount:
            payload["amount"] = amount

        logger.info(f"📤 Creating refund for order: {order_id}")
        logger.info(f"📤 Payload: {json.dumps(payload, indent=2)}")

        response = await client.post(
            f"{POLAR_API_BASE}/refunds/",
            headers={
                "Authorization": f"Bearer {POLAR_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        if response.status_code not in [200, 201]:
            error_msg = f"Polar API error: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

        result = response.json()
        logger.info(f"✅ Refund created: {result.get('id')}")
        return result


async def get_order(order_id: str) -> Dict[str, Any]:
    """
    Polar'dan order detaylarını getirir.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        logger.info(f"📤 Getting order: {order_id}")
        
        response = await client.get(
            f"{POLAR_API_BASE}/orders/{order_id}",
            headers={
                "Authorization": f"Bearer {POLAR_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            error_msg = f"Polar API error: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        result = response.json()
        logger.info(f"✅ Order found: {result.get('id')}")
        logger.info(f"💰 Total amount: {result.get('total_amount')}")
        logger.info(f"💰 Refundable amount: {result.get('refundable_amount')}")
        logger.info(f"💰 Net amount: {result.get('net_amount')}")
        
        # ✅ Fatura URL'lerini logla
        receipt_url = result.get('receipt_url')
        invoice_url = result.get('invoice_url')
        logger.info(f"📄 Receipt URL: {receipt_url}")
        logger.info(f"📄 Invoice URL: {invoice_url}")
        
        # ✅ Eğer URL yoksa, dashboard link'ini oluştur
        if not receipt_url and not invoice_url:
            organization_id = result.get('organization_id')
            if organization_id:
                # Dashboard link'ini oluştur
                dashboard_url = f"https://sandbox.polar.sh/dashboard/{organization_id}/sales/{order_id}"
                result['dashboard_url'] = dashboard_url
                logger.info(f"📄 Dashboard URL: {dashboard_url}")
        
        return result

def verify_webhook_signature(payload: bytes, webhook_id: str, webhook_timestamp: str, webhook_signature: str) -> bool:
    """
    Polar webhook imzasını doğrular.
    """
    try:
        import hmac
        import hashlib
        import base64
        from datetime import datetime, timezone
        
        if not POLAR_WEBHOOK_SECRET:
            logger.error("❌ POLAR_WEBHOOK_SECRET not set")
            return False
        
        # ✅ Secret'ı doğru şekilde kullan
        # Polar secret'ı genellikle whsec_ ile başlar ve base64 encoded'dir
        secret = POLAR_WEBHOOK_SECRET.encode('utf-8')
        
        # Eğer secret whsec_ ile başlıyorsa, base64 decode et
        if POLAR_WEBHOOK_SECRET.startswith("whsec_"):
            try:
                # whsec_ prefix'ini kaldır ve decode et
                secret_raw = POLAR_WEBHOOK_SECRET[6:]  # whsec_ kaldır
                # Eksik base64 padding'ini ekle
                missing_padding = len(secret_raw) % 4
                if missing_padding:
                    secret_raw += '=' * (4 - missing_padding)
                secret = base64.b64decode(secret_raw)
                logger.info("🔍 Secret decoded from base64 (whsec_ format)")
            except Exception as e:
                logger.warning(f"⚠️ Base64 decode failed: {e}, using raw secret")
                secret = POLAR_WEBHOOK_SECRET.encode('utf-8')
        else:
            # Doğrudan secret'ı kullan
            secret = POLAR_WEBHOOK_SECRET.encode('utf-8')
            logger.info("🔍 Using raw secret")
        
        # Mesajı oluştur: id + timestamp + payload
        message = f"{webhook_id}.{webhook_timestamp}.{payload.decode('utf-8')}".encode()
        
        # İmzayı hesapla
        expected_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        
        # Webhook'tan gelen imzayı temizle (v1, prefix'ini kaldır)
        if webhook_signature.startswith("v1,"):
            actual_signature = webhook_signature.split(",", 1)[1]
        else:
            actual_signature = webhook_signature
        
        logger.info(f"🔍 Expected: {expected_signature}")
        logger.info(f"🔍 Actual: {actual_signature}")
        
        # Zaman damgasını kontrol et (5 dakika)
        try:
            timestamp = int(webhook_timestamp)
            now = int(datetime.now(timezone.utc).timestamp())
            if abs(now - timestamp) > 300:
                logger.warning(f"⚠️ Webhook timestamp too old: {now} vs {timestamp}")
                return False
        except ValueError:
            pass
        
        # İmzaları karşılaştır
        result = hmac.compare_digest(expected_signature, actual_signature)
        logger.info(f"✅ Signature verification result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Webhook verification error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
