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
    billing_address = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    billing_state = Column(String, nullable=True)
    billing_country = Column(String, nullable=True, default="TR")
    billing_postal_code = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    tax_office = Column(String, nullable=True)
    identity_number = Column(String, nullable=True)
        
    # 🆕🆕 TREND & EXECUTIVE SUMMARY (YENİ)
    trend_summary = Column(JSONB, nullable=True)           # Trend Summary
    trend_updated_at = Column(DateTime, nullable=True)     # Trend güncellenme zamanı
    executive_summary = Column(JSONB, nullable=True)       # Executive Summary
    executive_updated_at = Column(DateTime, nullable=True) # Executive güncellenme zamanı


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
    
    # 🆕 AI ALANLARI
    ai_summary = Column(JSONB, nullable=True)          # AI özeti (tüm ürünleri kapsayan)
    ai_status = Column(String, nullable=True)          # 'pending', 'completed', 'failed'
    ai_version = Column(String, nullable=True)         # AI model sürümü (ör. 'gemini-1.5-flash')
    ai_created_at = Column(DateTime, nullable=True)    # Oluşturulma zamanı
    ai_prompt_version = Column(String, nullable=True)  # Prompt sürümü (versiyon yönetimi için)
    
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

# ============================================================
# 🆕 PROCESSING CREDIT MİMARİSİ - YENİ MODELLER
# ============================================================
    
    # Durum
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    description = Column(String, nullable=True)
    version = Column(String, default="1.0")

class ProcessingScoreRange(Base):
    """
    Processing Score -> İşlem Kredisi eşleştirme tablosu
    """
    __tablename__ = "processing_score_ranges"
    
    id = Column(Integer, primary_key=True, index=True)
    min_score = Column(Integer, nullable=False)  # Minimum Processing Score
    max_score = Column(Integer, nullable=False)  # Maksimum Processing Score
    credit_cost = Column(Integer, nullable=False)  # Bu aralığa denk gelen İşlem Kredisi
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisDataset(Base):
    """
    Dataset tablosu - Her analiz için oluşturulan veri kümesi
    """
    __tablename__ = "analysis_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String, nullable=True, index=True)  # Upload'dan gelen ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Dataset metrikleri
    product_count = Column(Integer, default=0)  # Ürün sayısı
    period_count = Column(Integer, default=0)  # Dönem sayısı (hafta)
    data_points = Column(Integer, default=0)  # ProductCount × PeriodCount
    
    # Dataset içeriği (JSON)
    dataset_data = Column(JSONB, nullable=False, default={})
    
    # Metadata
    source_type = Column(String, default="excel")  # excel, api, erp, csv
    source_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # İlişki
    user = relationship("User")


class ProcessingTransaction(Base):
    """
    İşlem Kredisi harcama log tablosu
    """
    __tablename__ = "processing_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("analysis_datasets.id"), nullable=True)
    endpoint = Column(String, nullable=False)
    
    # Hesaplama detayları
    processing_score = Column(Integer, nullable=False)
    credit_cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    
    # Performance
    elapsed_time_ms = Column(Float, nullable=True)  # Gerçek işlem süresi (ms)
    avg_time_per_unit_ms = Column(Float, nullable=True)  # Birim başına ortalama süre
    
    # Metadata
    status = Column(String, default="completed")  # completed, failed
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişki
    user = relationship("User")
    dataset = relationship("AnalysisDataset")

# ============================================================
# 🆕 ENDPOINT PROFILE MODELİ
# ============================================================

class EndpointProfile(Base):
    """
    Endpoint profil tablosu - Her endpoint'in fiyatlandırma profili
    """
    __tablename__ = "endpoint_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, unique=True, nullable=False, index=True)
    method = Column(String, default="POST")
    
    # Ücretlendirme parametreleri
    base_credit = Column(Integer, default=1)
    pricing_type = Column(String, default="DATA_POINTS")  # FIXED, DATA_POINTS, DATA_POINTS_ITERATION, AI_USAGE, CUSTOM, COMPLEX
    algorithm_weight = Column(Float, default=1.0)
    avg_time_per_unit = Column(Float, default=0.0)
    
    # 🆕 Dataset konfigürasyonu (JSONB)
    dataset_config = Column(JSONB, default={}, nullable=False)
    # Örnek:
    # {
    #   "datasets": [
    #     {"table": "materials", "weight": 1.0, "type": "data_points"},
    #     {"table": "material_suppliers", "weight": 1.5, "type": "relation"},
    #     {"table": "suppliers", "weight": 0.5, "type": "lookup"}
    #   ]
    # }
    
    # Durum
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    description = Column(String, nullable=True)
    version = Column(String, default="1.0")

# app/models.py - DOSYA SONUNA EKLE

# ============================================================
# 🆕 SMART IMPORT ENGINE - VALIDATION MODELS
# ============================================================

class ValidationRule(Base):
    """Veri doğrulama kuralları - Admin panelinden yönetilir"""
    __tablename__ = "validation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String, nullable=False, index=True)  # column_check, data_type, business_rule, consistency
    table_name = Column(String, nullable=True)  # Temel_Veriler, Tedarikciler, Malzeme_Tedarikciler
    column_name = Column(String, nullable=True)
    rule_config = Column(JSONB, nullable=False, default={})
    severity = Column(String, default="warning")  # error, warning, info
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisImpactRule(Base):
    """Analiz etki kuralları - Hangi alan hangi analizi etkiler"""
    __tablename__ = "analysis_impact_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String, nullable=False, index=True)  # forecast, safety_stock, supplier, simulation, backtest
    field_name = Column(String, nullable=False)
    importance = Column(String, nullable=False)  # critical, recommended, optional, not_used
    description = Column(String, nullable=True)
    min_weeks_required = Column(Integer, nullable=True)  # Forecast için 12, Safety Stock için 8, vb.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NormalizationRule(Base):
    """Akıllı veri standardizasyonu kuralları"""
    __tablename__ = "normalization_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String, nullable=False)
    pattern = Column(String, nullable=False)  # regex pattern
    replacement = Column(String, nullable=True)
    confidence_threshold = Column(Float, default=0.8)  # 0-1 arası, bu eşiğin altı otomatik düzeltilmez
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ValidationResult(Base):
    """Import Wizard sonuçları - Geçici olarak saklanır"""
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    upload_id = Column(String, nullable=False, index=True)
    step = Column(Integer, default=1)  # 1-6 arası
    result_data = Column(JSONB, nullable=False, default={})
    status = Column(String, default="in_progress")  # in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 24 saat sonra temizlenir
