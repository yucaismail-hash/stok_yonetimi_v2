from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, TokenHistory, UserTokenTransaction, Sector, CreditTransaction, Notification
from app.auth import get_current_user, get_password_hash, verify_password
from app.services import polar as polar_service
from app.services.polar import POLAR_API_BASE, POLAR_ACCESS_TOKEN
import re
import io
import base64
import httpx
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_country: Optional[str] = None
    billing_postal_code: Optional[str] = None
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    identity_number: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class SupportTicketCreate(BaseModel):
    subject: str
    message: str
    priority: str = "medium"


# ============================================
# 📌 MEVCUT ENDPOINT'LER
# ============================================

@router.get("/")
async def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı profil bilgilerini getir (fatura bilgileri dahil)"""
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
        "sector_name": sector_name,
        "token_balance": current_user.token_balance,
        "created_at": current_user.created_at,
        "billing_address": current_user.billing_address,
        "billing_city": current_user.billing_city,
        "billing_state": current_user.billing_state,
        "billing_country": current_user.billing_country,
        "billing_postal_code": current_user.billing_postal_code,
        "tax_id": current_user.tax_id,
        "tax_office": current_user.tax_office,
        "identity_number": current_user.identity_number
    }

@router.put("/")
async def update_profile(
    profile: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı profilini güncelle (fatura bilgileri dahil)"""
    update_data = profile.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
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
            "token_balance": current_user.token_balance,
            "billing_address": current_user.billing_address,
            "billing_city": current_user.billing_city,
            "billing_state": current_user.billing_state,
            "billing_country": current_user.billing_country,
            "billing_postal_code": current_user.billing_postal_code,
            "tax_id": current_user.tax_id,
            "tax_office": current_user.tax_office,
            "identity_number": current_user.identity_number
        }
    }


@router.post("/change-password")
async def change_password(
    request: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı şifresini değiştir"""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre yanlış")
    
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")
    
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Şifreler eşleşmiyor")
    
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    return {"success": True, "message": "Şifre başarıyla değiştirildi"}


# ============================================
# 🆕 İŞLEM GEÇMİŞİ (İADELER DAHİL)
# ============================================

@router.get("/transactions")
async def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    transaction_type: Optional[str] = None
):
    """
    Token işlem geçmişini getir (satın alma + harcama + iade)
    """
    query = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == current_user.id,
        CreditTransaction.transaction_type.in_(['purchase', 'refund', 'bonus'])
    )
    
    if transaction_type:
        query = query.filter(CreditTransaction.transaction_type == transaction_type)
    
    total = query.count()
    transactions = query.order_by(CreditTransaction.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.transaction_type,
                "description": t.description,
                "balance_after": current_user.token_balance,
                "created_at": t.created_at,
                "price": t.price,
                "polar_order_id": t.polar_order_id
            }
            for t in transactions
        ]
    }


# ============================================
# 🆕 POLAR FATURA PDF
# ============================================

@router.get("/transaction/{transaction_id}/polar-invoice")
async def get_polar_invoice(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Polar'dan fatura PDF'ini getir.
    """
    # 1. İşlemi bul
    transaction = db.query(CreditTransaction).filter(
        CreditTransaction.id == transaction_id,
        CreditTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="İşlem bulunamadı")
    
    if not transaction.polar_order_id:
        raise HTTPException(status_code=404, detail="Polar order ID bulunamadı")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Fatura oluşturmayı dene (Generate Invoice)
            generate_response = await client.post(
                f"{POLAR_API_BASE}/orders/{transaction.polar_order_id}/invoice",
                headers={
                    "Authorization": f"Bearer {POLAR_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if generate_response.status_code not in [200, 201, 202]:
                print(f"⚠️ Fatura oluşturma hatası: {generate_response.status_code}")
            
            # 2. Receipt URL'ini al (PDF indirme linki)
            receipt_response = await client.get(
                f"{POLAR_API_BASE}/orders/{transaction.polar_order_id}/receipt",
                headers={
                    "Authorization": f"Bearer {POLAR_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if receipt_response.status_code == 200:
                data = receipt_response.json()
                receipt_url = data.get("url")
                
                if receipt_url:
                    pdf_response = await client.get(receipt_url)
                    if pdf_response.status_code == 200:
                        pdf_base64 = base64.b64encode(pdf_response.content).decode('utf-8')
                        return {
                            "success": True,
                            "pdf_base64": pdf_base64,
                            "filename": f"fatura_{transaction.polar_order_id[:8]}.pdf",
                            "type": "receipt"
                        }
            
            # 3. Invoice URL'ini dene (alternatif)
            invoice_response = await client.get(
                f"{POLAR_API_BASE}/orders/{transaction.polar_order_id}/invoice",
                headers={
                    "Authorization": f"Bearer {POLAR_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            
            if invoice_response.status_code == 200:
                data = invoice_response.json()
                invoice_url = data.get("url")
                
                if invoice_url:
                    pdf_response = await client.get(invoice_url)
                    if pdf_response.status_code == 200:
                        pdf_base64 = base64.b64encode(pdf_response.content).decode('utf-8')
                        return {
                            "success": True,
                            "pdf_base64": pdf_base64,
                            "filename": f"fatura_{transaction.polar_order_id[:8]}.pdf",
                            "type": "invoice"
                        }
        
        # 4. Hiçbir şey olmadıysa, dashboard link'ini döndür
        order = await polar_service.get_order(transaction.polar_order_id)
        organization_id = order.get("organization_id")
        if organization_id:
            dashboard_url = f"https://sandbox.polar.sh/dashboard/{organization_id}/sales/{transaction.polar_order_id}"
            return {
                "success": True,
                "dashboard_url": dashboard_url,
                "message": "Fatura oluşturulamadı. Lütfen Polar dashboard'dan indirin.",
                "type": "dashboard"
            }
        
        raise HTTPException(status_code=404, detail="Fatura bulunamadı")
        
    except Exception as e:
        print(f"❌ Fatura hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 🆕 DESTEK TALEBİ SİSTEMİ
# ============================================

@router.post("/support-ticket")
async def create_support_ticket(
    ticket: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Destek talebi oluştur"""
    from app.models import SupportTicket
    
    new_ticket = SupportTicket(
        user_id=current_user.id,
        subject=ticket.subject,
        message=ticket.message,
        priority=ticket.priority,
        status="open"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # Admin'e bildirim gönder
    admin = db.query(User).filter(User.email.in_(['admin@stok.com', 'admin@admin.com'])).first()
    if admin:
        notification = Notification(
            user_id=admin.id,
            title=f"📩 Yeni Destek Talebi: {ticket.subject}",
            message=f"Kullanıcı {current_user.email} tarafından yeni bir destek talebi oluşturuldu.",
            type="info",
            link="/admin/support-tickets"
        )
        db.add(notification)
        db.commit()
    
    return {
        "success": True,
        "message": "Destek talebiniz başarıyla oluşturuldu.",
        "ticket_id": new_ticket.id
    }


@router.get("/support-tickets")
async def get_support_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """Kullanıcının destek taleplerini getir"""
    from app.models import SupportTicket
    
    query = db.query(SupportTicket).filter(
        SupportTicket.user_id == current_user.id
    )
    
    total = query.count()
    tickets = query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "tickets": [
            {
                "id": t.id,
                "subject": t.subject,
                "message": t.message,
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at,
                "resolved_at": t.resolved_at
            }
            for t in tickets
        ]
    }