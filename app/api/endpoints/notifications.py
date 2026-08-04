from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any  # ✅ EKLENDİ
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import *
from app.auth import get_current_user
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationCreate(BaseModel):
    user_id: Optional[int] = None
    title: str
    message: str
    type: str = "info"
    link: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    link: Optional[str]
    created_at: datetime


# ============================================
# 📨 BİLDİRİM API'LERİ
# ============================================

@router.get("/")
async def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    unread_only: bool = False
):
    """Kullanıcının bildirimlerini getir"""
    query = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    )
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    return {
        "success": True,
        "total": len(notifications),
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "link": n.link,
                "created_at": n.created_at
            }
            for n in notifications
        ]
    }


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Okunmamış bildirim sayısını getir"""
    count = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None)),
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bildirimi okundu olarak işaretle"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Bildirim bulunamadı")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Bildirim okundu olarak işaretlendi"}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm bildirimleri okundu olarak işaretle"""
    db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None)),
        Notification.is_read == False
    ).update({"is_read": True, "read_at": datetime.utcnow()})
    db.commit()
    
    return {"success": True, "message": "Tüm bildirimler okundu olarak işaretlendi"}


@router.post("/admin/send")
async def send_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin tarafından bildirim gönder (Admin yetkisi gerekli)"""
    admin_emails = ["admin@stok.com", "admin@admin.com"]
    if current_user.email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    new_notification = Notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        link=notification.link
    )
    db.add(new_notification)
    db.commit()
    
    if notification.user_id:
        background_tasks.add_task(
            send_email_notification,
            notification.user_id,
            notification.title,
            notification.message,
            db
        )
    
    return {
        "success": True,
        "message": "Bildirim gönderildi",
        "notification_id": new_notification.id
    }


@router.post("/notify-task-completed")
async def notify_task_completed(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """ASYNC görev tamamlandığında bildirim oluştur"""
    try:
        user_id = request.get("user_id")
        task_id = request.get("task_id")
        task_type = request.get("task_type")
        
        if not user_id or not task_id:
            return {"success": False, "error": "Eksik parametreler"}
        
        task_names = {
            'forecast_batch_async': 'Talep Tahmini',
            'backtest_batch_async': 'Backtest',
            'simulation_batch_async': 'Monte Carlo Simülasyonu',
            'supplier_batch_async': 'Tedarikçi Analizi',
            'safety_stock_batch_async': 'Emniyet Stoğu',
        }
        
        task_name = task_names.get(task_type, 'Analiz')
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "Kullanıcı bulunamadı"}
        
        notification = Notification(
            user_id=user_id,
            title=f"✅ {task_name} Tamamlandı!",
            message=f"{task_name} raporunuz başarıyla oluşturuldu. (#{task_id[:8]})",
            type="success",
            link="/tasks"
        )
        db.add(notification)
        db.commit()
        
        print(f"✅ Bildirim kaydedildi: User {user_id}, Task {task_id}")
        
        background_tasks.add_task(
            send_email_notification,
            user_id,
            f"{task_name} Tamamlandı!",
            f"{task_name} raporunuz başarıyla oluşturuldu.\n\nİşlem No: #{task_id[:8]}\n\nRaporu görüntülemek için ASYNC Görevler sayfasına gidin.",
            db
        )
        
        return {"success": True, "message": "Bildirim oluşturuldu"}
        
    except Exception as e:
        print(f"❌ Bildirim oluşturma hatası: {e}")
        return {"success": False, "error": str(e)}


# ============================================
# 📧 E-POSTA GÖNDERME
# ============================================

def send_email_notification(user_id: int, title: str, message: str, db: Session):
    """E-posta bildirimi gönder"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            return
        
        SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
        SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
        SMTP_USER = os.getenv("SMTP_USER", "")
        SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        
        if not SMTP_USER or not SMTP_PASSWORD:
            print("⚠️ SMTP ayarları eksik, e-posta gönderilemedi")
            return
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1976d2; color: white; padding: 15px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 Stok Yönetim Sistemi</h2>
                </div>
                <div class="content">
                    <h3>{title}</h3>
                    <p>{message}</p>
                    <p style="margin-top: 20px; font-size: 14px; color: #666;">
                        Bu e-posta otomatik olarak gönderilmiştir.
                    </p>
                </div>
                <div class="footer">
                    &copy; 2024 Stok Yönetim Sistemi
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 {title}"
        msg["From"] = SMTP_USER
        msg["To"] = user.email
        
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            
        print(f"✅ E-posta gönderildi: {user.email}")
        
    except Exception as e:
        print(f"❌ E-posta gönderme hatası: {e}")