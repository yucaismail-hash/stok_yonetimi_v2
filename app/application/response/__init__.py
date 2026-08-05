# app/application/response/__init__.py
"""
Response - DOCUMENT 07 APP-005 / REVISION 05

ResponseBuilder SHALL become responsible for:
- Standard response generation
- Metadata
- Execution identifiers
- Error formatting
- Response schema consistency
"""

from app.application.response.response_builder import ResponseBuilder
from app.application.response.schemas import APIResponse, ResponseMetadata, ErrorDetail

__all__ = [
    "ResponseBuilder",
    "APIResponse",
    "ResponseMetadata",
    "ErrorDetail",
]