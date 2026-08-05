# app/models/company.py
"""
Company and User models.
Follows DOCUMENT 03 - Database Architecture Specification.
DOCUMENT 06A Integration: AI Artifact relationships.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.models.base import BaseModel
from app.database import Base


class Company(BaseModel):
    """Company entity - DOCUMENT 03 Section 4: Multi-tenant isolation."""
    __tablename__ = "companies"

    name = Column(String, nullable=False)
    tax_id = Column(String, unique=True, nullable=True)
    tax_office = Column(String, nullable=True)
    identity_number = Column(String, nullable=True)
    
    # Billing info
    billing_address = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    billing_state = Column(String, nullable=True)
    billing_country = Column(String, nullable=True, default="TR")
    billing_postal_code = Column(String, nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, nullable=True, default={})

    # ====================================================================
    # RELATIONSHIPS
    # ====================================================================
    
    # Mevcut ilişkiler
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="company", cascade="all, delete-orphan")
    analysis_datasets = relationship("AnalysisDataset", back_populates="company", cascade="all, delete-orphan")
    execution_results = relationship("ExecutionResult", back_populates="company")
    learning_data = relationship("UserLearningData", back_populates="company")
    company_learning = relationship("CompanyLearningMemory", back_populates="company")
    encryption_key = relationship("CompanyEncryptionKey", back_populates="company", uselist=False)
    
    # DOCUMENT 06A - AI Artifact ilişkisi (tek bir tanım)
    ai_artifacts = relationship(
        "AIArtifact",
        back_populates="company",
        cascade="all, delete-orphan"
    )


class User(BaseModel):
    """User entity - belongs to a Company."""
    __tablename__ = "users"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="user")  # admin, user, viewer
    
    # User preferences
    language = Column(String, default="TR")
    timezone = Column(String, default="UTC")
    
    # Trend & Executive Summary
    trend_summary = Column(JSONB, nullable=True)
    trend_updated_at = Column(DateTime, nullable=True)
    executive_summary = Column(JSONB, nullable=True)
    executive_updated_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="users")
    sector = relationship("Sector", back_populates="users")
    
    # Existing relationships
    materials = relationship("UserMaterial", back_populates="user", cascade="all, delete-orphan")
    results = relationship("AnalysisResult", back_populates="user")
    uploads = relationship("UploadedData", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    support_tickets = relationship("SupportTicket", back_populates="user")
    token_history = relationship("TokenHistory", back_populates="user")
    token_transactions = relationship("UserTokenTransaction", back_populates="user")
    credit_transactions = relationship("CreditTransaction", back_populates="user")
    learning_data = relationship("UserLearningData", back_populates="user")
    company_learning = relationship("CompanyLearningMemory", back_populates="user")
    encryption_key = relationship("CompanyEncryptionKey", back_populates="user", uselist=False)


class Sector(BaseModel):
    __tablename__ = "sectors"

    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    # Relationships
    users = relationship("User", back_populates="sector")
    products = relationship("ProductGroup", back_populates="sector")


class ProductGroup(BaseModel):
    __tablename__ = "product_groups"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    sector_id = Column(PG_UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)

    # Relationships
    sector = relationship("Sector", back_populates="products")
    materials = relationship("UserMaterial", back_populates="product_group")


class Supplier(BaseModel):
    __tablename__ = "suppliers"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    factor = Column(Integer, default=1.0)
    risk_score = Column(Integer, default=0.5)
    performance_score = Column(Integer, default=0.7)
    lt_mean = Column(Integer, default=14.0)
    lt_std = Column(Integer, default=3.0)

    # Relationships
    material_suppliers = relationship("MaterialSupplier", back_populates="supplier")


class UserMaterial(BaseModel):
    __tablename__ = "user_materials"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    material_code = Column(String, nullable=False)
    material_name = Column(String, nullable=True)
    group = Column(String, nullable=True)
    
    lead_time_days = Column(Integer, default=14)
    unit_cost = Column(Integer, default=100.0)
    holding_rate = Column(Integer, default=0.2)
    shortage_cost = Column(Integer, default=500.0)
    initial_stock = Column(Integer, default=0)
    eoq = Column(Integer, default=100)
    weekly_demand = Column(JSONB, default=[])
    
    product_group_id = Column(PG_UUID(as_uuid=True), ForeignKey("product_groups.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="materials")
    company = relationship("Company")
    product_group = relationship("ProductGroup", back_populates="materials")
    suppliers = relationship("MaterialSupplier", back_populates="material")


class MaterialSupplier(BaseModel):
    __tablename__ = "material_suppliers"

    material_id = Column(PG_UUID(as_uuid=True), ForeignKey("user_materials.id"))
    supplier_id = Column(PG_UUID(as_uuid=True), ForeignKey("suppliers.id"))
    share = Column(Integer, default=1.0)
    is_primary = Column(Boolean, default=False)

    # Relationships
    material = relationship("UserMaterial", back_populates="suppliers")
    supplier = relationship("Supplier", back_populates="material_suppliers")