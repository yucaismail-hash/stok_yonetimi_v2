# app/models/learning.py
"""
Learning models - Company Learning Memory and User Learning Data.
Based on modelsx.py structure.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # ✅ EKLENDI
from datetime import datetime

from app.database import Base


class UserLearningData(Base):
    __tablename__ = "user_learning_data"

    id = Column(Integer, primary_key=True)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
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

    user = relationship("User", back_populates="learning_data")
    company = relationship("Company", back_populates="learning_data")


class CompanyLearningMemory(Base):
    """
    Şirket Hafızası - Learning Engine tarafından öğrenilen davranış kalıpları
    """
    __tablename__ = "company_learning_memory"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Kural Bilgileri
    rule_id = Column(String, unique=True, nullable=False, index=True)
    rule_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)  # seasonal, intermittent, lead_time, trend, supplier, successful_method

    # Kural Detayları
    description = Column(Text, nullable=True)
    pattern_data = Column(JSONB, nullable=True)

    # İstatistikler
    confidence_score = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # Zaman Bilgileri
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)

    # Durum
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişki
    user = relationship("User", back_populates="company_learning")
    company = relationship("Company", back_populates="company_learning")


class PatternIntelligence(Base):
    __tablename__ = "pattern_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_group_id = Column(Integer, ForeignKey("product_groups.id"), nullable=True)
    pattern_type = Column(String, nullable=False)
    pattern_params = Column(JSONB, nullable=True)
    confidence_score = Column(Float, default=0.0)
    company_learning_id = Column(Integer, ForeignKey("company_learning_memory.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_calculated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SectorIntelligence(Base):
    __tablename__ = "sector_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
    pattern_type = Column(String, nullable=False)
    pattern_params = Column(JSONB, nullable=True)
    confidence_score = Column(Float, default=0.0)
    company_count = Column(Integer, default=0)
    anonymized_data = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)
    last_calculated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KnowledgeMaturity(Base):
    __tablename__ = "knowledge_maturity"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    company_learning_maturity = Column(Float, default=0.0)
    pattern_intelligence_maturity = Column(Float, default=0.0)
    sector_intelligence_maturity = Column(Float, default=0.0)
    overall_maturity = Column(Float, default=0.0)
    total_learning_records = Column(Integer, default=0)
    verified_patterns = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    maturity_level = Column(String, default="beginner")
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('company_learning_maturity >= 0 AND company_learning_maturity <= 100', name='check_company_learning_maturity_range'),
        CheckConstraint('pattern_intelligence_maturity >= 0 AND pattern_intelligence_maturity <= 100', name='check_pattern_intelligence_maturity_range'),
        CheckConstraint('sector_intelligence_maturity >= 0 AND sector_intelligence_maturity <= 100', name='check_sector_intelligence_maturity_range'),
        CheckConstraint('overall_maturity >= 0 AND overall_maturity <= 100', name='check_overall_maturity_range'),
    )


class CompanyAIMemory(Base):
    __tablename__ = "company_ai_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision_type = Column(String, nullable=False)
    decision_input = Column(JSONB, nullable=True)
    decision_output = Column(JSONB, nullable=False)
    user_feedback = Column(String, nullable=True)
    user_notes = Column(Text, nullable=True)
    actual_outcome = Column(JSONB, nullable=True)
    outcome_success = Column(Boolean, nullable=True)
    outcome_measured_at = Column(DateTime(timezone=True), nullable=True)
    confidence_before = Column(Float, default=0.0)
    confidence_after = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
