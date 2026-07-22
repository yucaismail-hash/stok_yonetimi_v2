# app/schemas/dataset.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class DatasetMetadata(BaseModel):
    """Dataset metrikleri"""
    product_count: int = 0
    period_count: int = 0
    data_points: int = 0
    source_type: str = "excel"
    source_name: Optional[str] = None


class DatasetCreate(BaseModel):
    """Dataset oluşturma isteği"""
    user_id: int
    upload_id: Optional[str] = None
    materials: List[Dict[str, Any]]
    suppliers: Optional[Dict[str, Any]] = None
    supplier_mapping: Optional[Dict[str, Any]] = None
    week_columns: Optional[List[str]] = None
    source_type: str = "excel"
    source_name: Optional[str] = None


class DatasetResponse(BaseModel):
    """Dataset yanıtı"""
    id: int
    upload_id: Optional[str]
    user_id: int
    product_count: int
    period_count: int
    data_points: int
    source_type: str
    source_name: Optional[str]
    dataset_data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool


class DatasetSummary(BaseModel):
    """Dataset özet bilgisi"""
    id: int
    product_count: int
    period_count: int
    data_points: int
    source_type: str
    created_at: datetime