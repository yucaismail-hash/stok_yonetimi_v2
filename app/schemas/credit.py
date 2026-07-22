# app/schemas/credit.py - TAM DOSYA (GÜNCELLENMİŞ)

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============================================================
# MEVCUT ŞEMALAR
# ============================================================

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


# ============================================================
# POLAR ENTEGRASYONU ŞEMALARI
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
# 🆕 DATASET CONFIG ŞEMALARI
# ============================================================

class DatasetConfigItem(BaseModel):
    """Dataset konfigürasyonu öğesi"""
    table: str
    weight: float = 1.0
    type: str = "data_points"  # data_points, relation, lookup, custom


class DatasetConfig(BaseModel):
    """Dataset konfigürasyonu"""
    datasets: List[DatasetConfigItem]


# ============================================================
# 🆕 ENDPOINT PROFILE ŞEMALARI - GÜNCELLENMİŞ
# ============================================================

class EndpointProfileCreate(BaseModel):
    endpoint: str
    method: str = "POST"
    base_credit: int = 1
    pricing_type: str = "DATA_POINTS"
    algorithm_weight: float = 1.0
    avg_time_per_unit: float = 0.0
    description: Optional[str] = None
    is_active: bool = True
    dataset_config: Optional[Dict[str, Any]] = None


class EndpointProfileUpdate(BaseModel):
    base_credit: Optional[int] = None
    pricing_type: Optional[str] = None
    algorithm_weight: Optional[float] = None
    avg_time_per_unit: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    dataset_config: Optional[Dict[str, Any]] = None


class EndpointProfileResponse(BaseModel):
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
    dataset_config: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


# ============================================================
# 🆕 PRICING PREVIEW RESPONSE - GÜNCELLENMİŞ
# ============================================================

class PricingPreviewResponse(BaseModel):
    endpoint: str
    dataset_id: int
    product_count: int
    period_count: int
    data_points: int
    algorithm_weight: float
    processing_score: int
    estimated_credit_cost: int
    current_balance: int
    is_sufficient: bool
    calculation_method: Optional[str] = "data_points"
    breakdown: Optional[Dict[str, Any]] = None


# ============================================================
# 📌 PRICING REQUEST / RESPONSE - GÜNCELLENMİŞ
# ============================================================

class PricingRequest(BaseModel):
    endpoint: str
    dataset_id: int
    user_id: int


class PricingResponse(BaseModel):
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
    calculation_method: Optional[str] = "data_points"
    breakdown: Optional[Dict[str, Any]] = None


# ============================================================
# PROCESSING SCORE RANGE ŞEMALARI
# ============================================================

class ProcessingScoreRangeCreate(BaseModel):
    min_score: int
    max_score: int
    credit_cost: int
    description: Optional[str] = None
    is_active: bool = True


class ProcessingScoreRangeUpdate(BaseModel):
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    credit_cost: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProcessingScoreRangeResponse(BaseModel):
    id: int
    min_score: int
    max_score: int
    credit_cost: int
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================
# PROCESSING TRANSACTION ŞEMALARI
# ============================================================

class ProcessingTransactionResponse(BaseModel):
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