# app/integration/__init__.py
"""
Integration Layer - DOCUMENT 07 PART 04

External systems SHALL communicate only through Integration Adapters.
Integration Adapters SHALL translate external requests into Application Commands.
"""

from app.integration.adapters import BaseAdapter, ERPAdapter
from app.integration.pipelines.import_pipeline import ImportPipeline
from app.integration.mapping.field_mapper import FieldMapper
from app.integration.mapping.mapping_registry import MappingRegistry
from app.integration.mapping.mapping_engine import MappingEngine
from app.integration.errors import (
    IntegrationError,
    ConnectionError,
    AuthenticationError,
    ValidationError,
    TransformationError,
    MappingError,
    SynchronizationError,
    TimeoutError,
    RetryLimitExceeded,
    ErrorHandler,
)

__all__ = [
    # Adapters
    "BaseAdapter",
    "ERPAdapter",
    # Pipelines
    "ImportPipeline",
    # Mapping
    "FieldMapper",
    "MappingRegistry",
    "MappingEngine",
    # Sync
    # Errors
    "IntegrationError",
    "ConnectionError",
    "AuthenticationError",
    "ValidationError",
    "TransformationError",
    "MappingError",
    "SynchronizationError",
    "TimeoutError",
    "RetryLimitExceeded",
    "ErrorHandler",
]
