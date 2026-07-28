# app/schemas/import_wizard.py
"""
Import Wizard Schemas - Request ve Response modelleri
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional


class ReValidateRequest(BaseModel):
    """Re-validation için request modeli"""
    upload_id: str
    corrections: Dict[str, Any]


class NormalizeRequest(BaseModel):
    """Normalization için request modeli"""
    upload_id: str


class ApplyDatasetRequest(BaseModel):
    """Dataset oluşturma için request modeli"""
    upload_id: str