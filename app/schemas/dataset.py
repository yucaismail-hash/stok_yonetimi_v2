# app/schemas/dataset.py
"""
Dataset Pydantic Schemas
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class DatasetBase(BaseModel):
    """Base dataset schema."""
    source_type: str
    source_name: Optional[str] = None
    operation_type: str = "append"


class DatasetCreate(DatasetBase):
    """Create dataset schema."""
    data: Dict[str, Any] = Field(..., description="Dataset data (will be encrypted)")


class DatasetResponse(BaseModel):
    """Dataset response schema."""
    id: int
    user_id: int
    dataset_hash: str
    dataset_version: int
    source_type: str
    source_name: Optional[str] = None
    state: str
    operation_type: str
    record_count: int
    sku_count: int
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    data: Optional[Dict[str, Any]] = None
    status_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Dataset list response."""
    total: int
    skip: int
    limit: int
    items: List[DatasetResponse]


class DatasetValidateResponse(BaseModel):
    """Dataset validation response."""
    dataset_id: int
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    requires_approval: bool = False
    status: str
    message: str


class DatasetApproveResponse(BaseModel):
    """Dataset approval response."""
    dataset_id: int
    version: int
    status: str
    message: str
    diff_summary: Dict[str, Any]


class DatasetVersionResponse(BaseModel):
    """Dataset version response."""
    id: int
    dataset_id: int
    version_number: int
    dataset_hash: str
    record_count: int
    sku_count: int
    created_by: int
    created_at: datetime
    is_current: bool
    is_archived: bool


class DatasetDiffResponse(BaseModel):
    """Dataset diff response."""
    dataset_id: int
    previous_dataset_id: Optional[int] = None
    new_skus: List[str] = []
    removed_skus: List[str] = []
    modified_skus: List[str] = []
    modified_historical_values: List[Dict] = []
    missing_periods: List[Dict] = []
    duplicate_records: List[Dict] = []
    total_changes: int = 0
    requires_approval: bool = False
    executed_at: datetime