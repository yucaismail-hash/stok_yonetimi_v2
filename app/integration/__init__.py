# app/integration/__init__.py
"""
Integration Layer - DOCUMENT 07 PART 04

External systems SHALL communicate only through Integration Adapters.
Integration Adapters SHALL translate external requests into Application Commands.
"""

from app.integration.adapters import (
    BaseAdapter,
    ERPAdapter,
    ECommerceAdapter,
    CustomAdapter,
)
from app.integration.pipelines import (
    ImportPipeline,
    ExportPipeline,
)
from app.integration.mapping import (
    FieldMapper,
    MappingRegistry,
    MappingEngine,
)
from app.integration.sync import (
    SyncOrchestrator,
    ManualSync,
    ScheduledSync,
    EventDrivenSync,
)
from app.integration.lifecycle import LifecycleManager
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
    "ECommerceAdapter",
    "CustomAdapter",
    # Pipelines
    "ImportPipeline",
    "ExportPipeline",
    # Mapping
    "FieldMapper",
    "MappingRegistry",
    "MappingEngine",
    # Sync
    "SyncOrchestrator",
    "ManualSync",
    "ScheduledSync",
    "EventDrivenSync",
    # Lifecycle
    "LifecycleManager",
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