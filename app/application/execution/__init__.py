# app/application/execution/__init__.py
"""
Execution - DOCUMENT 07 APP-011 / APP-012
ExecutionContext and ExecutionResult definitions.
"""

from app.application.execution.execution_context import (
    ExecutionContext,
    ExecutionStatus,
    ExecutionObjectiveType,
    ExecutionAnalysisType,
)
from app.application.execution.execution_result import ExecutionResult

__all__ = [
    "ExecutionContext",
    "ExecutionStatus",
    "ExecutionObjectiveType",
    "ExecutionAnalysisType",
    "ExecutionResult",
]