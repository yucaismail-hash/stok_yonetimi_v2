# app/models/dataset.py
"""
Dataset models - Single source of truth for business data.
Follows DOCUMENT 03 - Database Architecture Specification.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text, Enum, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel
from app.database import Base


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
    """Analysis dataset - from modelsx.py"""
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
    """DOCUMENT 02 - Dataset Definition"""
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


    # ✅ JSON yerine JSONB
    diff_result = Column(JSONB, nullable=True)  # DOCUMENT 03 - JSONB Strategy
    previous_version_id = Column(PG_UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    
    # ✅ JSON yerine JSONB
    affected_skus = Column(JSONB, nullable=True)  # DOCUMENT 03 - JSONB Strategy
    
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

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