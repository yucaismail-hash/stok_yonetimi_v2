# app/engine/__init__.py
"""
Execution Engine - DOCUMENT 04
"""

from app.engine.enums import (
    TaskType,
    ExecutionState,
    BusinessObjective,
    TaskPriority,
    TaskStatus,
)

from app.engine.business_objectives import (
    BusinessObjectiveDefinition,
    WorkflowStep,
    get_objective,
    list_objectives,
    OBJECTIVE_REGISTRY,
)

from app.engine.workflow_generator import (
    Workflow,
    Task,
    WorkflowGenerator,
)

from app.engine.workflow_engine import (
    WorkflowEngine,
    WorkflowTemplate,
    DependencyResolution,
    DependencyType,
)

# DOCUMENT 04A - Foundation Extensions
from app.engine.execution_events import (
    ExecutionEvent,
    ExecutionEventType,
    EventPublisher,
    event_publisher,
)
from app.engine.capability_registry import (
    Capability,
    CapabilityRegistry,
    CapabilityRegistration,
    capability_registry,
)
from app.engine.execution_policy import (
    ExecutionPolicy,
    RetryConfig,
    TimeoutConfig,
    ParallelExecutionConfig,
    RetryPolicy,
    TimeoutPolicy,
    default_execution_policy,
)

__all__ = [
    # Enums
    "TaskType",
    "ExecutionState",
    "BusinessObjective",
    "TaskPriority",
    "TaskStatus",
    "DependencyType",
    # Business Objectives
    "BusinessObjectiveDefinition",
    "WorkflowStep",
    "get_objective",
    "list_objectives",
    "OBJECTIVE_REGISTRY",
    # Workflow Generator
    "Workflow",
    "Task",
    "WorkflowGenerator",
    # Workflow Engine
    "WorkflowEngine",
    "WorkflowTemplate",
    "DependencyResolution",
    # DOCUMENT 04A
    "ExecutionEvent",
    "ExecutionEventType",
    "EventPublisher",
    "event_publisher",
    "Capability",
    "CapabilityRegistry",
    "CapabilityRegistration",
    "capability_registry",
    "ExecutionPolicy",
    "RetryConfig",
    "TimeoutConfig",
    "ParallelExecutionConfig",
    "RetryPolicy",
    "TimeoutPolicy",
    "default_execution_policy",
]