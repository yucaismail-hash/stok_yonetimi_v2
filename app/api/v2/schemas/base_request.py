# app/api/v2/schemas/base_request.py
"""
Base Request Schema - DOCUMENT 07 APP-018 / REVISION 04

All request schemas SHALL inherit from this base model.
This guarantees a consistent API contract throughout the platform.

Every execution request SHALL contain:
- request_id
- company_id
- dataset_id
- command
- configuration
- language
- client_version
"""

from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """
    Base Request Schema - All requests SHALL inherit from this.
    """
    
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    company_id: UUID = Field(..., description="Company ID for multi-tenant isolation")
    dataset_id: UUID = Field(..., description="Dataset ID")
    language: Optional[str] = Field("tr", description="Response language")
    client_version: Optional[str] = Field(None, description="Client version")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for duplicate prevention")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "dataset_id": "123e4567-e89b-12d3-a456-426614174001",
                "language": "tr",
                "client_version": "1.0.0"
            }
        }


class BusinessObjectiveRequest(BaseRequest):
    """
    Business Objective Request Schema.
    
    Business Objective executions SHALL NOT specify analytical engines.
    Workflow Engine SHALL determine which engines are required.
    """
    
    objective_type: str = Field(..., description="Business objective type: forecast, safety_stock, simulation, supplier, backtest, seasonal_analysis, trend_analysis")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution configuration")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "dataset_id": "123e4567-e89b-12d3-a456-426614174001",
                "objective_type": "forecast",
                "language": "tr",
                "params": {
                    "forecast_horizon": 12,
                    "confidence_level": 0.95
                }
            }
        }


class SingleAnalysisRequest(BaseRequest):
    """
    Single Analysis Request Schema.
    
    Single Analysis requests SHALL also use Workflow Dispatcher.
    The execution flow SHALL remain identical.
    """
    
    analysis_type: str = Field(..., description="Analysis type: forecast, safety_stock, simulation, supplier, backtest")
    material_codes: Optional[list[str]] = Field(None, description="Optional list of material codes to analyze")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution configuration")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "dataset_id": "123e4567-e89b-12d3-a456-426614174001",
                "analysis_type": "forecast",
                "language": "tr",
                "material_codes": ["MAT-001", "MAT-002"],
                "params": {
                    "forecast_horizon": 12
                }
            }
        }


class DatasetUploadRequest(BaseRequest):
    """
    Dataset Upload Request Schema.
    """
    
    source_type: str = Field(..., description="Source type: excel, csv, api")
    source_name: Optional[str] = Field(None, description="Source name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dataset metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "dataset_id": "123e4567-e89b-12d3-a456-426614174001",
                "source_type": "excel",
                "source_name": "Q4_Sales_Data.xlsx"
            }
        }


class DatasetValidateRequest(BaseRequest):
    """
    Dataset Validate Request Schema.
    """
    
    dataset_id: UUID = Field(..., description="Dataset ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "dataset_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }


class DatasetApproveRequest(BaseRequest):
    """
    Dataset Approve Request Schema.
    """
    
    dataset_id: UUID = Field(..., description="Dataset ID")
    notes: Optional[str] = Field(None, description="Approval notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "dataset_id": "123e4567-e89b-12d3-a456-426614174001",
                "notes": "Dataset validated and approved for execution"
            }
        }