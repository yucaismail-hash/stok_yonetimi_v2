#!/usr/bin/env python3
"""
TEK DOSYA MIGRATION - DOCUMENT 03 UYUMLU
UUID, Company, Soft Delete ile

Kullanım:
    python migrate.py

Bu dosya:
    1. Veritabanını temizler
    2. Tüm tabloları DOCUMENT 03'e uygun şekilde oluşturur
    3. UUID primary key kullanır
    4. Company bazlı multi-tenant yapı kurar
    5. Soft Delete stratejisi uygular
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from uuid import uuid4
import enum

# ✅ .env dosyasını yükle
load_dotenv()

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# 1. SQLALCHEMY IMPORT'LARI
# ============================================

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, 
    DateTime, ForeignKey, JSON, Text, Enum, BigInteger,
    UniqueConstraint, Index, event, inspect, text,
    CheckConstraint  # ✅ EKLENDI
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ============================================
# 2. BASE MODEL - UUID + Soft Delete
# ============================================

class BaseModel(Base):
    __abstract__ = True

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================
# 3. TÜM MODELLER (DOCUMENT 03 UYUMLU)
# ============================================

class Company(BaseModel):
    __tablename__ = "companies"

    name = Column(String, nullable=False)
    tax_id = Column(String, unique=True, nullable=True)
    tax_office = Column(String, nullable=True)
    identity_number = Column(String, nullable=True)
    billing_address = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    billing_state = Column(String, nullable=True)
    billing_country = Column(String, nullable=True, default="TR")
    billing_postal_code = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, nullable=True, default={})

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="company", cascade="all, delete-orphan")
    analysis_datasets = relationship("AnalysisDataset", back_populates="company", cascade="all, delete-orphan")
    execution_results = relationship("ExecutionResult", back_populates="company")
    learning_data = relationship("UserLearningData", back_populates="company")
    company_learning = relationship("CompanyLearningMemory", back_populates="company")
    encryption_key = relationship("CompanyEncryptionKey", back_populates="company", uselist=False)


class User(BaseModel):
    __tablename__ = "users"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="user")
    language = Column(String, default="TR")
    timezone = Column(String, default="UTC")
    token_balance = Column(Integer, default=100)
    polar_customer_id = Column(String, nullable=True, index=True)
    sector_id = Column(PG_UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    trend_summary = Column(JSONB, nullable=True)
    trend_updated_at = Column(DateTime, nullable=True)
    executive_summary = Column(JSONB, nullable=True)
    executive_updated_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="users")
    sector = relationship("Sector", back_populates="users")
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
    factor = Column(Float, default=1.0)
    risk_score = Column(Float, default=0.5)
    performance_score = Column(Float, default=0.7)
    lt_mean = Column(Float, default=14.0)
    lt_std = Column(Float, default=3.0)

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
    unit_cost = Column(Float, default=100.0)
    holding_rate = Column(Float, default=0.2)
    shortage_cost = Column(Float, default=500.0)
    initial_stock = Column(Float, default=0)
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
    share = Column(Float, default=1.0)
    is_primary = Column(Boolean, default=False)

    # Relationships
    material = relationship("UserMaterial", back_populates="suppliers")
    supplier = relationship("Supplier", back_populates="material_suppliers")


class DatasetState(str, enum.Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    APPROVED = "approved"
    ENCRYPTED = "encrypted"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class DatasetOperationType(str, enum.Enum):
    APPEND = "append"
    REVISION = "revision"
    REPLACEMENT = "replacement"


class AnalysisDataset(BaseModel):
    __tablename__ = "analysis_datasets"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)
    product_count = Column(Integer, default=0)
    period_count = Column(Integer, default=0)
    data_points = Column(Integer, default=0)
    dataset_data = Column(JSONB, nullable=False, default={})
    source_type = Column(String, default="excel")
    source_name = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="analysis_datasets")
    company = relationship("Company", back_populates="analysis_datasets")


class Dataset(BaseModel):
    __tablename__ = "datasets"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dataset_hash = Column(String(64), nullable=False, unique=True)
    dataset_version = Column(Integer, nullable=False, default=1)
    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=True)
    state = Column(Enum(DatasetState), nullable=False, default=DatasetState.UPLOADED)
    operation_type = Column(Enum(DatasetOperationType), nullable=False, default=DatasetOperationType.APPEND)
    uploaded_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    record_count = Column(Integer, nullable=False, default=0)
    sku_count = Column(Integer, nullable=False, default=0)
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    encrypted_data = Column(Text, nullable=True)
    encryption_key_id = Column(PG_UUID(as_uuid=True), ForeignKey("company_encryption_keys.id"), nullable=True)
    diff_result = Column(JSONB, nullable=True)
    previous_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    affected_skus = Column(JSONB, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    company = relationship("Company", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")
    events = relationship("DatasetEvent", back_populates="dataset", cascade="all, delete-orphan")
    validations = relationship("DatasetValidationResult", back_populates="dataset", cascade="all, delete-orphan")
    diff_results = relationship("DatasetDiffResult", foreign_keys="[DatasetDiffResult.dataset_id]", back_populates="dataset", cascade="all, delete-orphan")
    previous_diff_results = relationship("DatasetDiffResult", foreign_keys="[DatasetDiffResult.previous_dataset_id]", back_populates="previous_dataset")
    cache_entries = relationship("ExecutionCache", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('dataset_version >= 1', name='check_dataset_version_positive'),
        UniqueConstraint('company_id', 'dataset_hash', 'dataset_version', name='unique_company_dataset_version'),
    )


class DatasetVersion(BaseModel):
    __tablename__ = "dataset_versions"

    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    dataset_hash = Column(String(64), nullable=False)
    record_count = Column(Integer, nullable=False)
    sku_count = Column(Integer, nullable=False)
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    previous_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("dataset_versions.id"), nullable=True)
    is_current = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)

    dataset = relationship("Dataset", back_populates="versions")


class DatasetEvent(BaseModel):
    __tablename__ = "dataset_events"

    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    event_type = Column(String, nullable=False)
    event_data = Column(JSONB, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    dataset = relationship("Dataset", back_populates="events")


class DatasetValidationResult(BaseModel):
    __tablename__ = "dataset_validation_results"

    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    is_valid = Column(Boolean, nullable=False, default=False)
    errors = Column(JSONB, nullable=True)
    warnings = Column(JSONB, nullable=True)
    validated_by = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), server_default=func.now())
    changes_requiring_approval = Column(JSONB, nullable=True)
    auto_approved_changes = Column(JSONB, nullable=True)
    requires_user_approval = Column(Boolean, default=False)

    dataset = relationship("Dataset", back_populates="validations")


class DatasetDiffResult(BaseModel):
    __tablename__ = "dataset_diff_results"

    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    previous_dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    new_skus = Column(JSONB, nullable=True)
    removed_skus = Column(JSONB, nullable=True)
    modified_skus = Column(JSONB, nullable=True)
    modified_historical_values = Column(JSONB, nullable=True)
    missing_periods = Column(JSONB, nullable=True)
    duplicate_records = Column(JSONB, nullable=True)
    total_changes = Column(Integer, default=0)
    requires_approval = Column(Boolean, default=False)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", foreign_keys=[dataset_id], back_populates="diff_results")
    previous_dataset = relationship("Dataset", foreign_keys=[previous_dataset_id], back_populates="previous_diff_results")


class CompanyEncryptionKey(BaseModel):
    __tablename__ = "company_encryption_keys"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, unique=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    key_version = Column(String, default="1")
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, default=1)

    # Relationships
    company = relationship("Company", back_populates="encryption_key")
    user = relationship("User", back_populates="encryption_key")


class WorkflowExecution(BaseModel):
    __tablename__ = "workflow_executions"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    objective_type = Column(String, nullable=False)
    objective_params = Column(JSONB, nullable=True)
    status = Column(String(20), default="pending")
    current_stage = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    functional_dependencies = Column(JSONB, nullable=True)
    enrichment_dependencies = Column(JSONB, nullable=True)
    skipped_enrichments = Column(JSONB, nullable=True)
    final_result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    company = relationship("Company")
    dataset = relationship("Dataset")
    tasks = relationship("WorkflowTask", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowTask(BaseModel):
    __tablename__ = "workflow_tasks"

    workflow_id = Column(PG_UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False)
    task_type = Column(String, nullable=False)
    task_order = Column(Integer, nullable=False)
    depends_on = Column(JSONB, nullable=True)
    is_functional = Column(Boolean, default=True)
    status = Column(String(20), default="pending")
    result_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    record_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow = relationship("WorkflowExecution", back_populates="tasks")


class AnalysisResult(BaseModel):
    __tablename__ = "analysis_results"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)
    result_type = Column(String, nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    params = Column(JSONB, default={})
    task_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    message = Column(String, nullable=True)
    total_materials = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    ai_summary = Column(JSONB, nullable=True)
    ai_status = Column(String, nullable=True)
    ai_version = Column(String, nullable=True)
    ai_created_at = Column(DateTime, nullable=True)
    ai_prompt_version = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="results")
    company = relationship("Company", back_populates="execution_results")


class ExecutionResult(BaseModel):
    __tablename__ = "execution_results"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    objective_type = Column(String, nullable=False)
    workflow_id = Column(String, nullable=False)
    task_id = Column(String, nullable=True)
    result_type = Column(String, nullable=False)
    result_data = Column(JSONB, nullable=False)
    params = Column(JSONB, nullable=True)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    message = Column(String(500), nullable=True)
    total_materials = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    ai_summary = Column(JSONB, nullable=True)
    ai_status = Column(String(50), nullable=True)
    ai_version = Column(String(50), nullable=True)
    ai_created_at = Column(DateTime(timezone=True), nullable=True)
    ai_prompt_version = Column(String(50), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    company = relationship("Company")
    dataset = relationship("Dataset")

    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
    )


class ExecutionMetrics(BaseModel):
    __tablename__ = "execution_metrics"

    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("execution_results.id"), nullable=False, unique=True)
    total_duration_ms = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    ram_usage_mb = Column(Float, nullable=True)
    peak_ram_mb = Column(Float, nullable=True)
    algorithm_version = Column(String, nullable=True)
    worker_info = Column(String, nullable=True)
    total_api_calls = Column(Integer, default=0)
    total_token_cost = Column(Integer, default=0)

    __table_args__ = (
        CheckConstraint('total_duration_ms >= 0', name='check_duration_positive'),
        CheckConstraint('cpu_usage_percent >= 0', name='check_cpu_positive'),
        CheckConstraint('ram_usage_mb >= 0', name='check_ram_positive'),
    )


class ExecutionStageMetrics(BaseModel):
    __tablename__ = "execution_stage_metrics"

    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("execution_results.id"), nullable=False)
    stage_name = Column(String, nullable=False)
    duration_ms = Column(Float, nullable=True)
    record_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)


class ExecutionResourceMetrics(BaseModel):
    __tablename__ = "execution_resource_metrics"

    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("execution_results.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_value = Column(Float, nullable=False)
    unit = Column(String, default="percent")


class ExecutionCache(BaseModel):
    __tablename__ = "execution_cache"

    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    sku_code = Column(String, nullable=False)
    result_type = Column(String, nullable=False)
    result_data = Column(JSONB, nullable=False)
    result_hash = Column(String(64), nullable=False)
    algorithm_version = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_valid = Column(Boolean, default=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="cache_entries")


class UserLearningData(BaseModel):
    __tablename__ = "user_learning_data"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    sector_id = Column(PG_UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    learning_key = Column(String, unique=True, nullable=False)
    pattern_multiplier = Column(Float, default=1.0)
    seasonal_multiplier = Column(Float, default=1.0)
    confidence = Column(Float, default=0.0)
    sample_count = Column(Integer, default=0)
    pattern = Column(String, nullable=True)
    learning_type = Column(String, default="group")

    # Relationships
    user = relationship("User", back_populates="learning_data")
    company = relationship("Company", back_populates="learning_data")


class CompanyLearningMemory(BaseModel):
    __tablename__ = "company_learning_memory"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    rule_id = Column(String, unique=True, nullable=False, index=True)
    rule_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pattern_data = Column(JSONB, nullable=True)
    confidence_score = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="company_learning")
    company = relationship("Company", back_populates="company_learning")


class TokenCost(BaseModel):
    __tablename__ = "token_costs"

    endpoint = Column(String, nullable=False)
    method = Column(String, default="POST")
    cost = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)


class TokenHistory(BaseModel):
    __tablename__ = "token_history"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    endpoint = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    # Relationships
    user = relationship("User", back_populates="token_history")


class UserTokenTransaction(BaseModel):
    __tablename__ = "user_token_transactions"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    endpoint = Column(String, nullable=True)
    balance_after = Column(Integer, nullable=False)

    # Relationships
    user = relationship("User", back_populates="token_transactions")


class CreditPackage(BaseModel):
    __tablename__ = "credit_packages"

    polar_product_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    price_tl = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)


class CreditTransaction(BaseModel):
    __tablename__ = "credit_transactions"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
    tax = Column(Float, nullable=True, default=0)
    transaction_type = Column(String, nullable=False)
    polar_order_id = Column(String, nullable=True, index=True)
    polar_product_id = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="credit_transactions")


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")
    is_read = Column(Boolean, default=False)
    link = Column(String, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")


class SupportTicket(BaseModel):
    __tablename__ = "support_tickets"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default="open")
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="support_tickets")


class UploadedData(BaseModel):
    __tablename__ = "uploaded_data"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String, default="excel")
    processed_data = Column(JSONB, default={})
    raw_data = Column(JSONB, default={})
    processed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")

    # Relationships
    user = relationship("User", back_populates="uploads")


class AnalysisInput(BaseModel):
    __tablename__ = "analysis_inputs"

    upload_id = Column(String, unique=True, nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    data = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)


class AnalysisBatchResult(BaseModel):
    __tablename__ = "analysis_batch_results"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)
    result_type = Column(String, nullable=False, index=True)
    result_data = Column(JSONB, nullable=False)
    params = Column(JSONB, default={})
    total_materials = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)


class AnalysisMaterialSummary(BaseModel):
    __tablename__ = "analysis_material_summary"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)
    batch_id = Column(PG_UUID(as_uuid=True), ForeignKey("analysis_batch_results.id"), nullable=True)
    material_code = Column(String, nullable=False, index=True)
    material_group = Column(String, nullable=True)
    result_type = Column(String, nullable=False, index=True)
    summary = Column(JSONB, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class EndpointProfile(BaseModel):
    __tablename__ = "endpoint_profiles"

    endpoint = Column(String, unique=True, nullable=False)
    method = Column(String, default="POST")
    base_credit = Column(Integer, default=1)
    pricing_type = Column(String, default="DATA_POINTS")
    algorithm_weight = Column(Float, default=1.0)
    avg_time_per_unit = Column(Float, default=0.0)
    dataset_config = Column(JSONB, default={}, nullable=False)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    version = Column(String, default="1.0")


class ProcessingScoreRange(BaseModel):
    __tablename__ = "processing_score_ranges"

    min_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    credit_cost = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class ProcessingTransaction(BaseModel):
    __tablename__ = "processing_transactions"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dataset_id = Column(PG_UUID(as_uuid=True), ForeignKey("analysis_datasets.id"), nullable=True)
    endpoint = Column(String, nullable=False)
    processing_score = Column(Integer, nullable=False)
    credit_cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    elapsed_time_ms = Column(Float, nullable=True)
    avg_time_per_unit_ms = Column(Float, nullable=True)
    status = Column(String, default="completed")
    error_message = Column(String, nullable=True)

    # Relationships
    user = relationship("User")
    dataset = relationship("AnalysisDataset")


class ValidationRule(BaseModel):
    __tablename__ = "validation_rules"

    rule_type = Column(String, nullable=False, index=True)
    table_name = Column(String, nullable=True)
    column_name = Column(String, nullable=True)
    rule_config = Column(JSONB, nullable=False, default={})
    severity = Column(String, default="warning")
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)


class AnalysisImpactRule(BaseModel):
    __tablename__ = "analysis_impact_rules"

    analysis_type = Column(String, nullable=False, index=True)
    field_name = Column(String, nullable=False)
    importance = Column(String, nullable=False)
    description = Column(String, nullable=True)
    min_weeks_required = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)


class NormalizationRule(BaseModel):
    __tablename__ = "normalization_rules"

    rule_name = Column(String, nullable=False)
    pattern = Column(String, nullable=False)
    replacement = Column(String, nullable=True)
    confidence_threshold = Column(Float, default=0.8)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)


class ValidationResult(BaseModel):
    __tablename__ = "validation_results"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=False, index=True)
    step = Column(Integer, default=1)
    result_data = Column(JSONB, nullable=False, default={})
    status = Column(String, default="in_progress")
    expires_at = Column(DateTime, nullable=True)


class ExternalCache(BaseModel):
    __tablename__ = "external_cache"

    cache_key = Column(String, unique=True, nullable=False, index=True)
    service_name = Column(String, nullable=False)
    cached_data = Column(JSONB, nullable=False)
    data_hash = Column(String(16), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    is_valid = Column(Boolean, default=True)
    hit_count = Column(Integer, default=0)


# ============================================
# AUDIT MODELS
# ============================================

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    event_type = Column(String, nullable=False)
    event_category = Column(String, nullable=False, default="business")
    description = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=True)
    target_type = Column(String, nullable=True)
    target_id = Column(PG_UUID(as_uuid=True), nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)


class SecurityEvent(BaseModel):
    __tablename__ = "security_events"
    
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="medium")
    description = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=True)
    source_ip = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    method = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)


# ============================================
# SYSTEM MODELS
# ============================================

class AlgorithmVersion(BaseModel):
    __tablename__ = "algorithm_versions"
    
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    parameters = Column(JSONB, nullable=True, default={})
    is_active = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(String, nullable=True)
    released_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('name', 'version', name='unique_algorithm_name_version'),
    )


class FeatureFlag(BaseModel):
    __tablename__ = "feature_flags"
    
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=False)
    scope = Column(String, default="global")
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rollout_percentage = Column(Float, default=100.0)
    rollout_started_at = Column(DateTime(timezone=True), nullable=True)
    rollout_ended_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('key', name='unique_feature_flag_key'),
    )


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"
    
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    value = Column(JSONB, nullable=False)
    value_type = Column(String, default="string")
    category = Column(String, default="general")
    is_active = Column(Boolean, default=True)
    is_editable = Column(Boolean, default=True)
    updated_by = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('key', name='unique_system_setting_key'),
    )


# ============================================
# 4. MIGRATION FONKSİYONU
# ============================================

def run_migration():
    """Tüm migration'ı tek seferde çalıştır."""
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    logger.info(f"Veritabanına bağlanılıyor: {database_url[:50]}...")
    
    try:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        
        # Bağlantıyı test et
        with engine.connect() as conn:
            logger.info("✅ Veritabanı bağlantısı başarılı")
        
        # ✅ UUID extension'ı kontrol et
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\""))
            conn.commit()
            logger.info("✅ pgcrypto extension aktif")
        
        # ✅ Tüm tabloları oluştur
        logger.info("📦 Tablolar oluşturuluyor...")
        Base.metadata.create_all(engine)
        logger.info("✅ Tüm tablolar başarıyla oluşturuldu")
        
        # Özet bilgi
        logger.info("\n" + "="*50)
        logger.info("📊 MIGRATION ÖZETİ")
        logger.info("="*50)
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Toplam tablo sayısı: {len(tables)}")
        
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            logger.info(f"  📋 {table}: {len(columns)} kolon")
        
        logger.info("="*50)
        logger.info("✅ MIGRATION TAMAMLANDI!")
        logger.info(f"   Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration hatası: {str(e)}")
        return False


# ============================================
# 5. ANA PROGRAM
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  STOKONOMI AI - DOCUMENT 03 MIGRATION")
    print("  UUID + Company + Soft Delete")
    print("="*60 + "\n")
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration başarıyla tamamlandı!")
        sys.exit(0)
    else:
        print("\n❌ Migration başarısız oldu!")
        sys.exit(1)