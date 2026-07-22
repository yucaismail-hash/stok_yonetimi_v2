# app/schemas/__init__.py

# ============================================================
# ESKİ ŞEMALAR (app/schemas.py'den taşındı)
# ============================================================

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TokenCostCreate(BaseModel):
    endpoint: str
    method: str = "POST"
    cost: int = 1
    is_active: bool = True


class TokenCostUpdate(BaseModel):
    cost: Optional[int] = None
    is_active: Optional[bool] = None


class TokenCostResponse(BaseModel):
    id: int
    endpoint: str
    method: str
    cost: int
    is_active: bool
    updated_at: datetime


class UserTokenUpdate(BaseModel):
    user_id: int
    token_balance: int


class SupplierCreate(BaseModel):
    code: str
    name: str
    factor: float = 1.0


class MaterialSupplierCreate(BaseModel):
    supplier_id: int
    share: float = 1.0
    is_primary: bool = False


class MaterialCreate(BaseModel):
    code: str
    name: str
    group: str
    lead_time_days: int
    unit_cost: float
    holding_rate: float
    shortage_cost: float
    initial_stock: float
    weekly_demand: List[float]
    eoq: float


# ============================================================
# POLAR ENTEGRASYONU İÇİN ŞEMALAR
# ============================================================

class CreditPackageCreate(BaseModel):
    polar_product_id: str
    name: str
    credits: int
    price_tl: float


class CreditPackageUpdate(BaseModel):
    name: Optional[str] = None
    credits: Optional[int] = None
    price_tl: Optional[float] = None
    is_active: Optional[bool] = None


class CreditPackageResponse(BaseModel):
    id: int
    polar_product_id: str
    name: str
    credits: int
    price_tl: float
    is_active: bool


class CheckoutRequest(BaseModel):
    product_id: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    product_id: str
    product_name: str


class CreditTransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: int
    transaction_type: str
    description: Optional[str]
    created_at: datetime


# ============================================================
# 🆕 PROCESSING CREDIT MİMARİSİ - YENİ ŞEMALAR
# ============================================================

# ----- DATASET ŞEMALARI -----

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
    materials: List[dict]
    suppliers: Optional[dict] = None
    supplier_mapping: Optional[dict] = None
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
    dataset_data: dict
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


# ----- ENDPOINT PROFİL ŞEMALARI -----

class EndpointProfileCreate(BaseModel):
    """Endpoint profili oluşturma"""
    endpoint: str
    method: str = "POST"
    base_credit: int = 1
    pricing_type: str = "DATA_POINTS"
    algorithm_weight: float = 1.0
    avg_time_per_unit: float = 0.0
    description: Optional[str] = None
    is_active: bool = True


class EndpointProfileUpdate(BaseModel):
    """Endpoint profili güncelleme"""
    base_credit: Optional[int] = None
    pricing_type: Optional[str] = None
    algorithm_weight: Optional[float] = None
    avg_time_per_unit: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class EndpointProfileResponse(BaseModel):
    """Endpoint profili yanıtı"""
    id: int
    endpoint: str
    method: str
    base_credit: int
    pricing_type: str
    algorithm_weight: float
    avg_time_per_unit: float
    is_active: bool
    description: Optional[str]
    version: str
    created_at: datetime
    updated_at: datetime


# ----- PROCESSING SCORE RANGE ŞEMALARI -----

class ProcessingScoreRangeCreate(BaseModel):
    """Processing Score aralığı oluşturma"""
    min_score: int
    max_score: int
    credit_cost: int
    description: Optional[str] = None
    is_active: bool = True


class ProcessingScoreRangeUpdate(BaseModel):
    """Processing Score aralığı güncelleme"""
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    credit_cost: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProcessingScoreRangeResponse(BaseModel):
    """Processing Score aralığı yanıtı"""
    id: int
    min_score: int
    max_score: int
    credit_cost: int
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ----- PROCESSING TRANSACTION ŞEMALARI -----

class ProcessingTransactionResponse(BaseModel):
    """İşlem Kredisi harcama log yanıtı"""
    id: int
    user_id: int
    dataset_id: Optional[int]
    endpoint: str
    processing_score: int
    credit_cost: int
    balance_after: int
    elapsed_time_ms: Optional[float]
    avg_time_per_unit_ms: Optional[float]
    status: str
    error_message: Optional[str]
    created_at: datetime


# ----- PRICING REQUEST / RESPONSE -----

class PricingRequest(BaseModel):
    """Pricing Engine'e gönderilen istek"""
    endpoint: str
    dataset_id: int
    user_id: int


class PricingResponse(BaseModel):
    """Pricing Engine'den dönen yanıt"""
    success: bool
    dataset_id: int
    endpoint: str
    product_count: int
    period_count: int
    data_points: int
    algorithm_weight: float
    processing_score: int
    credit_cost: int
    balance_before: int
    balance_after: int
    is_sufficient: bool
    message: Optional[str] = None


# ============================================================
# TÜM SINIFLARI DIŞA AÇ (Optional - IDE otomatik tamamlama için)
# ============================================================

__all__ = [
    # Eski şemalar
    'TokenCostCreate',
    'TokenCostUpdate',
    'TokenCostResponse',
    'UserTokenUpdate',
    'SupplierCreate',
    'MaterialSupplierCreate',
    'MaterialCreate',
    # Polar şemaları
    'CreditPackageCreate',
    'CreditPackageUpdate',
    'CreditPackageResponse',
    'CheckoutRequest',
    'CheckoutResponse',
    'CreditTransactionResponse',
    # Dataset şemaları
    'DatasetMetadata',
    'DatasetCreate',
    'DatasetResponse',
    'DatasetSummary',
    # Endpoint profil şemaları
    'EndpointProfileCreate',
    'EndpointProfileUpdate',
    'EndpointProfileResponse',
    # Processing Score Range şemaları
    'ProcessingScoreRangeCreate',
    'ProcessingScoreRangeUpdate',
    'ProcessingScoreRangeResponse',
    # Processing Transaction şemaları
    'ProcessingTransactionResponse',
    # Pricing şemaları
    'PricingRequest',
    'PricingResponse',
]