from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON, Text
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
    sector_id = Column(Integer, nullable=True)  # ForeignKey yok
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Tüm ilişkiler KALDIRILDI
    # sector = relationship("Sector", back_populates="users")
    # token_history = relationship("TokenHistory", back_populates="user")
    # purchases = relationship("TokenPurchase", back_populates="user")
    # analysis_results = relationship("UserAnalysisResult", back_populates="user")
    # learning_data = relationship("UserLearningData", back_populates="user")
    # materials = relationship("UserMaterial", back_populates="user")


class Sector(Base):
    __tablename__ = "sectors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Tüm ilişkiler KALDIRILDI
    # users = relationship("User", back_populates="sector")
    # product_groups = relationship("ProductGroup", back_populates="sector")


class ProductGroup(Base):
    __tablename__ = "product_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    # sector_id = Column(Integer, ForeignKey("sectors.id"))  # KALDIRILDI
    # sector = relationship("Sector", back_populates="product_groups")  # KALDIRILDI


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
    
    # materials = relationship("MaterialSupplier", back_populates="supplier")  # KALDIRILDI


class UserMaterial(Base):
    __tablename__ = "user_materials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Bu foreign key kalabilir (kullanıcı-malzeme ilişkisi)
    material_code = Column(String, nullable=False)
    material_name = Column(String, nullable=True)
    group = Column(String, nullable=True)
    # sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)  # KALDIRILDI
    # product_group_id = Column(Integer, ForeignKey("product_groups.id"), nullable=True)  # KALDIRILDI
    
    lead_time_days = Column(Integer, default=14)
    unit_cost = Column(Float, default=100.0)
    holding_rate = Column(Float, default=0.2)
    shortage_cost = Column(Float, default=500.0)
    initial_stock = Column(Float, default=0)
    eoq = Column(Integer, default=100)
    weekly_demand = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # user = relationship("User", back_populates="materials")  # KALDIRILDI
    # sector = relationship("Sector")  # KALDIRILDI
    # product_group = relationship("ProductGroup", back_populates="materials")  # KALDIRILDI
    # suppliers = relationship("MaterialSupplier", back_populates="material")  # KALDIRILDI


class MaterialSupplier(Base):
    __tablename__ = "material_suppliers"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("user_materials.id"))  # Bu foreign key kalabilir
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))  # Bu foreign key kalabilir
    share = Column(Float, default=1.0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # material = relationship("UserMaterial", back_populates="suppliers")  # KALDIRILDI
    # supplier = relationship("Supplier", back_populates="materials")  # KALDIRILDI


class UserAnalysisResult(Base):
    __tablename__ = "user_analysis_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Bu foreign key kalabilir
    
    result_type = Column(String, nullable=False)
    material_code = Column(String, nullable=True)
    material_group = Column(String, nullable=True)
    # sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)  # KALDIRILDI
    # product_group_id = Column(Integer, ForeignKey("product_groups.id"), nullable=True)  # KALDIRILDI
    
    result_data = Column(JSON, nullable=False)
    params = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # user = relationship("User", back_populates="analysis_results")  # KALDIRILDI
    # sector = relationship("Sector")  # KALDIRILDI
    # product_group = relationship("ProductGroup")  # KALDIRILDI


class UserLearningData(Base):
    __tablename__ = "user_learning_data"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Bu foreign key kalabilir
    
    learning_key = Column(String, unique=True, nullable=False)
    
    pattern_multiplier = Column(Float, default=1.0)
    seasonal_multiplier = Column(Float, default=1.0)
    
    confidence = Column(Float, default=0.0)
    sample_count = Column(Integer, default=0)
    
    # sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)  # KALDIRILDI
    # product_group_id = Column(Integer, ForeignKey("product_groups.id"), nullable=True)  # KALDIRILDI
    pattern = Column(String, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # user = relationship("User", back_populates="learning_data")  # KALDIRILDI
    # sector = relationship("Sector")  # KALDIRILDI
    # product_group = relationship("ProductGroup")  # KALDIRILDI


class TokenHistory(Base):
    __tablename__ = "token_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Bu foreign key kalabilir
    endpoint = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # user = relationship("User", back_populates="token_history")  # KALDIRILDI


class TokenPurchase(Base):
    __tablename__ = "token_purchases"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Bu foreign key kalabilir
    amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    payment_id = Column(String, nullable=True)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # user = relationship("User", back_populates="purchases")  # KALDIRILDI


class TokenCost(Base):
    __tablename__ = "token_costs"
    id = Column(Integer, primary_key=True)
    endpoint = Column(String, unique=True, nullable=False)
    method = Column(String, default="POST")
    cost = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# 🆕 YENİ EKLENEN SINIFLAR (Mevcut yapıya dokunulmaz)
# ============================================

class UploadedData(Base):
    """Kullanıcı tarafından yüklenen Excel verileri"""
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
    status = Column(String, default="pending")  # pending, processing, completed, failed


class AnalysisResult(Base):
    """Forecast ve diğer analiz sonuçları"""
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    result_type = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    task_id = Column(String, nullable=True, index=True)  # Async işlemler için

# app/models.py - Yeni modeller

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null = tüm kullanıcılar
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")  # info, success, warning, error
    is_read = Column(Boolean, default=False)
    link = Column(String, nullable=True)  # Tıklanınca gidilecek sayfa
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    # user = relationship("User", back_populates="notifications")  # İlişki kaldırıldı (diğerleriyle uyumlu)


class UserTokenTransaction(Base):
    __tablename__ = "user_token_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Pozitif = kazanç, Negatif = harcama
    type = Column(String, nullable=False)  # 'spend', 'purchase', 'bonus', 'refund'
    description = Column(String, nullable=False)
    endpoint = Column(String, nullable=True)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # user = relationship("User", back_populates="transactions")  # İlişki kaldırıldı