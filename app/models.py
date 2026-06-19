from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


# ==================== KULLANICI ====================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    token_balance = Column(Integer, default=100)
    full_name = Column(String, default="")
    company_name = Column(String, default="")
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)  # ✅ nullable=False yap
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    sector = relationship("Sector", back_populates="users")
    token_history = relationship("TokenHistory", back_populates="user")
    purchases = relationship("TokenPurchase", back_populates="user")
    analysis_results = relationship("UserAnalysisResult", back_populates="user")
    learning_data = relationship("UserLearningData", back_populates="user")
    materials = relationship("UserMaterial", back_populates="user")


# ==================== SEKTÖR ====================
class Sector(Base):
    __tablename__ = "sectors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="sector")
    product_groups = relationship("ProductGroup", back_populates="sector")


# ==================== ÜRÜN GRUBU ====================
class ProductGroup(Base):
    __tablename__ = "product_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    
    sector = relationship("Sector", back_populates="product_groups")
    materials = relationship("UserMaterial", back_populates="product_group")


# ==================== TEDARİKÇİ ====================
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
    
    materials = relationship("MaterialSupplier", back_populates="supplier")


# ==================== KULLANICI MALZEMELERİ ====================
class UserMaterial(Base):
    __tablename__ = "user_materials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    material_code = Column(String, nullable=False)
    material_name = Column(String, nullable=True)
    group = Column(String, nullable=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    product_group_id = Column(Integer, ForeignKey("product_groups.id"), nullable=True)
    
    lead_time_days = Column(Integer, default=14)
    unit_cost = Column(Float, default=100.0)
    holding_rate = Column(Float, default=0.2)
    shortage_cost = Column(Float, default=500.0)
    initial_stock = Column(Float, default=0)
    eoq = Column(Integer, default=100)
    weekly_demand = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="materials")
    sector = relationship("Sector")
    product_group = relationship("ProductGroup", back_populates="materials")
    suppliers = relationship("MaterialSupplier", back_populates="material")


# ==================== MALZEME-TEDARİKÇİ İLİŞKİSİ ====================
class MaterialSupplier(Base):
    __tablename__ = "material_suppliers"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("user_materials.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    share = Column(Float, default=1.0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    material = relationship("UserMaterial", back_populates="suppliers")
    supplier = relationship("Supplier", back_populates="materials")


# ==================== KULLANICI ANALİZ SONUÇLARI ====================
class UserAnalysisResult(Base):
    __tablename__ = "user_analysis_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    result_type = Column(String, nullable=False)
    material_code = Column(String, nullable=True)
    material_group = Column(String, nullable=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    product_group_id = Column(Integer, ForeignKey("product_groups.id"), nullable=True)
    
    result_data = Column(JSON, nullable=False)
    params = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    user = relationship("User", back_populates="analysis_results")
    sector = relationship("Sector")
    product_group = relationship("ProductGroup")


# ==================== KULLANICI ÖĞRENME VERİLERİ ====================
class UserLearningData(Base):
    __tablename__ = "user_learning_data"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    learning_key = Column(String, unique=True, nullable=False)
    
    pattern_multiplier = Column(Float, default=1.0)
    seasonal_multiplier = Column(Float, default=1.0)
    
    confidence = Column(Float, default=0.0)
    sample_count = Column(Integer, default=0)
    
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    product_group_id = Column(Integer, ForeignKey("product_groups.id"), nullable=True)
    pattern = Column(String, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="learning_data")
    sector = relationship("Sector")
    product_group = relationship("ProductGroup")


# ==================== TOKEN ====================
class TokenHistory(Base):
    __tablename__ = "token_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="token_history")


class TokenPurchase(Base):
    __tablename__ = "token_purchases"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    payment_id = Column(String, nullable=True)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="purchases")


class TokenCost(Base):
    __tablename__ = "token_costs"
    id = Column(Integer, primary_key=True)
    endpoint = Column(String, unique=True, nullable=False)
    method = Column(String, default="POST")
    cost = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)