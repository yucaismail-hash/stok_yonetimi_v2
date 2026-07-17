from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    token_balance = Column(Integer, default=100)
    full_name = Column(String, default="")
    company_name = Column(String, default="")
    sector_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    polar_customer_id = Column(String, nullable=True, index=True)
    
    # 🆕 FATURA BİLGİLERİ
    billing_address = Column(String, nullable=True)  # Adres
    billing_city = Column(String, nullable=True)     # Şehir
    billing_state = Column(String, nullable=True)    # İl/İlçe
    billing_country = Column(String, nullable=True, default="TR")  # Ülke
    billing_postal_code = Column(String, nullable=True)  # Posta kodu
    tax_id = Column(String, nullable=True)           # Vergi Numarası
    tax_office = Column(String, nullable=True)       # Vergi Dairesi
    identity_number = Column(String, nullable=True)  # TC Kimlik No / Vergi No


class Sector(Base):
    __tablename__ = "sectors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProductGroup(Base):
    __tablename__ = "product_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    factor = Column(Float, default=1.0)
    risk_score = Column(Float, default=0.5)
    performance_score = Column(Float, default=0.7)
    lt_mean = Column(Float, default=14.0)
    lt_std = Column(Float, default=3.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserMaterial(Base):
    __tablename__ = "user_materials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    material_code = Column(String, nullable=False)
    material_name = Column(String, nullable=True)
    group = Column(String, nullable=True)
    
    lead_time_days = Column(Integer, default=14)
    unit_cost = Column(Float, default=100.0)
    holding_rate = Column(Float, default=0.2)
    shortage_cost = Column(Float, default=500.0)
    initial_stock = Column(Float, default=0)
    eoq = Column(Integer, default=100)
    weekly_demand = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


class MaterialSupplier(Base):
    __tablename__ = "material_suppliers"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("user_materials.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    share = Column(Float, default=1.0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================
# ✅ GÜNCELLENMİŞ AnalysisResult (TEK TABLO - HEM SENKRON HEM ASYNC)
# ============================================================

class AnalysisResult(Base):
    """
    Tüm analiz sonuçları (Senkron + Async)
    - Senkron: task_id = NULL, status = NULL
    - Async: task_id = UUID, status = processing/completed/failed
    """
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)
    result_type = Column(String, nullable=False, index=True)
    
    # 📌 TÜM VERİ (JSONB)
    data = Column(JSONB, nullable=False)
    params = Column(JSONB, default={})
    
    # 📌 ASYNC TAKİP (NULL ise senkron)
    task_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True)  # processing, completed, failed
    progress = Column(Integer, default=0)
    message = Column(String, nullable=True)
    
    # 📌 METADATA
    total_materials = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # ✅ İlişki
    user = relationship("User")

class UserLearningData(Base):
    __tablename__ = "user_learning_data"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sector_id = Column(Integer, nullable=True)
    learning_key = Column(String, unique=True, nullable=False)    
    pattern_multiplier = Column(Float, default=1.0)
    seasonal_multiplier = Column(Float, default=1.0)    
    confidence = Column(Float, default=0.0)
    sample_count = Column(Integer, default=0)    
    pattern = Column(String, nullable=True)    
    learning_type = Column(String, default="group")  # "group" veya "material"
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TokenHistory(Base):
    __tablename__ = "token_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TokenCost(Base):
    __tablename__ = "token_costs"
    id = Column(Integer, primary_key=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, default="POST")
    cost = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UploadedData(Base):
    __tablename__ = "uploaded_data"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String, default="excel")
    processed_data = Column(JSON, default={})
    raw_data = Column(JSON, default={})
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")
    is_read = Column(Boolean, default=False)
    link = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)


class UserTokenTransaction(Base):
    __tablename__ = "user_token_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    endpoint = Column(String, nullable=True)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# 🆕 POLAR ENTEGRASYONU İÇİN YENİ MODELLER
# ============================================

class CreditPackage(Base):
    """Kredi paketleri - Polar Product ID ile eşleştirme"""
    __tablename__ = "credit_packages"
    id = Column(Integer, primary_key=True, index=True)
    polar_product_id = Column(String, unique=True, index=True, nullable=False)  # prod_xxx
    name = Column(String, nullable=False)  # "Starter", "Growth", "Business"
    credits = Column(Integer, nullable=False)  # 100, 250, 500
    price_tl = Column(Float, nullable=False)  # 1990, 4490, 7990
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Kredi miktarı
    price = Column(Float, nullable=True)      # KDV'siz fiyat (TL)
    tax = Column(Float, nullable=True, default=0)  # 🆕 KDV tutarı
    transaction_type = Column(String, nullable=False)  # "purchase", "refund", "bonus"
    polar_order_id = Column(String, nullable=True, index=True)
    polar_product_id = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# app/models.py - En alta ekleyin

class SupportTicket(Base):
    """Destek talepleri"""
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # user = relationship("User")  # İlişki kaldırıldı (mevcut yapıya uygun)

# ============================================
# 🆕 ANALYSIS INPUTS (KALICI VERİ SAKLAMA)
# ============================================

class AnalysisInput(Base):
    """Kullanıcı tarafından yüklenen Excel verileri (Kalıcı)"""
    __tablename__ = "analysis_inputs"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String, unique=True, index=True, nullable=False)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    data = Column(JSON, nullable=False)  # Tüm Excel verisi (materials, suppliers, mapping)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# app/models.py - En sona (SupportTicket'ten sonra) EKLEYİN

# ============================================
# 🆕 ANALYSIS BATCH RESULTS (TEK KAYIT)
# ============================================

class AnalysisBatchResult(Base):
    """Batch analiz sonuçları - Tüm veri TEK kayıtta"""
    __tablename__ = "analysis_batch_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)  # Hangi upload'dan geldiği
    result_type = Column(String, nullable=False, index=True)  # forecast_batch, safety_stock_batch, etc.
    
    # 📌 TEK JSON'da TÜM veri
    result_data = Column(JSON, nullable=False)  # Tüm malzemelerin sonuçları
    params = Column(JSON, default={})
    
    total_materials = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


# ============================================
# 🆕 ANALYSIS MATERIAL SUMMARY (Hafif Özet)
# ============================================

class AnalysisMaterialSummary(Base):
    """Malzeme bazlı analiz özetleri - Sadece önemli metrikler"""
    __tablename__ = "analysis_material_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)  # Hangi upload'dan geldiği
    batch_id = Column(Integer, ForeignKey("analysis_batch_results.id"), nullable=True)  # Hangi batch'ten
    
    material_code = Column(String, nullable=False, index=True)
    material_group = Column(String, nullable=True)
    result_type = Column(String, nullable=False, index=True)
    
    # 📌 Sadece ÖZET veri (hafif - AI için)
    summary = Column(JSON, nullable=False)  # {pattern, cv, trend, service_level, ...}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)