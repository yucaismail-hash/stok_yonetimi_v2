# app/api/v2/schemas/__init__.py
"""
API Schemas - DOCUMENT 07 APP-018 / APP-019

Request and Response schemas for all endpoints.
"""

from app.api.v2.schemas.base_request import (
    BaseRequest,
    BusinessObjectiveRequest,
    SingleAnalysisRequest,
    DatasetUploadRequest,
    DatasetValidateRequest,
    DatasetApproveRequest,
)
from app.api.v2.schemas.base_response import (
    BaseResponse,
    ResponseMetadata,
    ErrorDetail,
    ExecutionResponse,
    ArtifactResponse,
)

__all__ = [
    # Request schemas
    "BaseRequest",
    "BusinessObjectiveRequest",
    "SingleAnalysisRequest",
    "DatasetUploadRequest",
    "DatasetValidateRequest",
    "DatasetApproveRequest",
    # Response schemas
    "BaseResponse",
    "ResponseMetadata",
    "ErrorDetail",
    "ExecutionResponse",
    "ArtifactResponse",
]