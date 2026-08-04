# app/models/api.py
"""
API models - Token costs, credit transactions, notifications, etc.
Based on modelsx.py structure.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# ============================================
# TOKEN MODELS
# ============================================

class TokenCost(Base):
    __tablename__ = "token_costs"

    id = Column(Integer, primary_key=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, default="POST")
    cost = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TokenHistory(Base):
    __tablename__ = "token_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="token_history")


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

    user = relationship("User", back_populates="token_transactions")


# ============================================
# CREDIT MODELS
# ============================================

class CreditPackage(Base):
    __tablename__ = "credit_packages"

    id = Column(Integer, primary_key=True, index=True)
    polar_product_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    price_tl = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
    tax = Column(Float, nullable=True, default=0)
    transaction_type = Column(String, nullable=False)  # "purchase", "refund", "bonus"
    polar_order_id = Column(String, nullable=True, index=True)
    polar_product_id = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="credit_transactions")


# ============================================
# NOTIFICATION & SUPPORT
# ============================================

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

    user = relationship("User", back_populates="notifications")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="support_tickets")


# ============================================
# UPLOAD & ANALYSIS INPUT
# ============================================

class UploadedData(Base):
    __tablename__ = "uploaded_data"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String, default="excel")
    processed_data = Column(JSONB, default={})
    raw_data = Column(JSONB, default={})
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")

    user = relationship("User", back_populates="uploads")


class AnalysisInput(Base):
    __tablename__ = "analysis_inputs"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    data = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisBatchResult(Base):
    __tablename__ = "analysis_batch_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)
    result_type = Column(String, nullable=False, index=True)
    result_data = Column(JSONB, nullable=False)
    params = Column(JSONB, default={})
    total_materials = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class AnalysisMaterialSummary(Base):
    __tablename__ = "analysis_material_summary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, nullable=True, index=True)
    batch_id = Column(Integer, ForeignKey("analysis_batch_results.id"), nullable=True)
    material_code = Column(String, nullable=False, index=True)
    material_group = Column(String, nullable=True)
    result_type = Column(String, nullable=False, index=True)
    summary = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


# ============================================
# PROCESSING CREDIT MODELS
# ============================================

class EndpointProfile(Base):
    __tablename__ = "endpoint_profiles"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, unique=True, nullable=False, index=True)
    method = Column(String, default="POST")
    base_credit = Column(Integer, default=1)
    pricing_type = Column(String, default="DATA_POINTS")
    algorithm_weight = Column(Float, default=1.0)
    avg_time_per_unit = Column(Float, default=0.0)
    dataset_config = Column(JSONB, default={}, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(String, nullable=True)
    version = Column(String, default="1.0")


class ProcessingScoreRange(Base):
    __tablename__ = "processing_score_ranges"

    id = Column(Integer, primary_key=True, index=True)
    min_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    credit_cost = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProcessingTransaction(Base):
    __tablename__ = "processing_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("analysis_datasets.id"), nullable=True)
    endpoint = Column(String, nullable=False)
    processing_score = Column(Integer, nullable=False)
    credit_cost = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    elapsed_time_ms = Column(Float, nullable=True)
    avg_time_per_unit_ms = Column(Float, nullable=True)
    status = Column(String, default="completed")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    dataset = relationship("AnalysisDataset")


# ============================================
# VALIDATION MODELS
# ============================================

class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String, nullable=False, index=True)
    table_name = Column(String, nullable=True)
    column_name = Column(String, nullable=True)
    rule_config = Column(JSONB, nullable=False, default={})
    severity = Column(String, default="warning")
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisImpactRule(Base):
    __tablename__ = "analysis_impact_rules"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String, nullable=False, index=True)
    field_name = Column(String, nullable=False)
    importance = Column(String, nullable=False)  # critical, recommended, optional, not_used
    description = Column(String, nullable=True)
    min_weeks_required = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NormalizationRule(Base):
    __tablename__ = "normalization_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String, nullable=False)
    pattern = Column(String, nullable=False)
    replacement = Column(String, nullable=True)
    confidence_threshold = Column(Float, default=0.8)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    upload_id = Column(String, nullable=False, index=True)
    step = Column(Integer, default=1)
    result_data = Column(JSONB, nullable=False, default={})
    status = Column(String, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)