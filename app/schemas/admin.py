# app/schemas/admin.py - YENİ DOSYA

from pydantic import BaseModel
from typing import Optional, Dict, Any


# ============================================================
# VALIDATION RULE SCHEMAS
# ============================================================

class ValidationRuleCreate(BaseModel):
    rule_type: str
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    rule_config: Dict[str, Any] = {}
    severity: str = "warning"
    is_active: bool = True
    description: Optional[str] = None


class ValidationRuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


# ============================================================
# ANALYSIS IMPACT RULE SCHEMAS
# ============================================================

class AnalysisImpactRuleCreate(BaseModel):
    analysis_type: str
    field_name: str
    importance: str  # critical, recommended, optional, not_used
    description: Optional[str] = None
    min_weeks_required: Optional[int] = None
    is_active: bool = True


class AnalysisImpactRuleUpdate(BaseModel):
    analysis_type: Optional[str] = None
    field_name: Optional[str] = None
    importance: Optional[str] = None
    description: Optional[str] = None
    min_weeks_required: Optional[int] = None
    is_active: Optional[bool] = None


# ============================================================
# NORMALIZATION RULE SCHEMAS
# ============================================================

class NormalizationRuleCreate(BaseModel):
    rule_name: str
    pattern: str
    replacement: Optional[str] = None
    confidence_threshold: float = 0.8
    is_active: bool = True
    description: Optional[str] = None


class NormalizationRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    pattern: Optional[str] = None
    replacement: Optional[str] = None
    confidence_threshold: Optional[float] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None