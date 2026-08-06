"""Versioned, serializable contracts for the execution-engine boundary."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID

from app.engine.enums import ExecutionState


_ENGINE_STAGES = {
    "validation",
    "planning",
    "forecast",
    "safety_stock",
    "supplier",
    "simulation",
    "backtest",
    "completed",
}
_TERMINAL_STATES = {
    ExecutionState.COMPLETED,
    ExecutionState.FAILED,
    ExecutionState.CANCELLED,
}


def _require_uuid(value: UUID, field_name: str) -> None:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be a UUID instance")


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _require_aware_utc(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_json_safe(value: Any, field_name: str) -> None:
    try:
        _json_safe(value)
    except (TypeError, ValueError) as exc:
        raise type(exc)(f"{field_name} must be JSON-safe: {exc}") from exc


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("float values must be finite")
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        _require_aware_utc(value, "datetime value")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        return {
            _json_key(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    raise TypeError(f"unsupported value type {type(value).__name__}")


def _json_key(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("mapping keys must be strings")
    return value


@dataclass(frozen=True)
class WorkflowDispatchRequest:
    execution_id: UUID
    company_id: UUID
    user_id: UUID
    dataset_id: UUID
    objective_type: Optional[str] = None
    analysis_type: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    material_codes: Optional[List[str]] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for field_name in ("execution_id", "company_id", "user_id", "dataset_id"):
            _require_uuid(getattr(self, field_name), field_name)
        has_objective = isinstance(self.objective_type, str) and bool(self.objective_type.strip())
        has_analysis = isinstance(self.analysis_type, str) and bool(self.analysis_type.strip())
        if has_objective == has_analysis:
            raise ValueError("exactly one of objective_type or analysis_type must be non-empty")
        _require_non_empty(self.contract_version, "contract_version")
        _require_aware_utc(self.created_at, "created_at")
        _require_json_safe(self.params, "params")

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class WorkflowDispatchResult:
    execution_id: UUID
    workflow_id: str
    state: ExecutionState
    accepted_at: datetime
    message: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _require_uuid(self.execution_id, "execution_id")
        _require_non_empty(self.workflow_id, "workflow_id")
        if not isinstance(self.state, ExecutionState):
            raise TypeError("state must be an ExecutionState")
        _require_aware_utc(self.accepted_at, "accepted_at")
        _require_non_empty(self.contract_version, "contract_version")

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class RuntimeAcceptance:
    """Truthful runtime-registration outcome, distinct from execution completion."""

    execution_id: UUID
    workflow_id: str
    accepted: bool
    state: ExecutionState
    accepted_at: datetime
    message: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        _require_uuid(self.execution_id, "execution_id")
        _require_non_empty(self.workflow_id, "workflow_id")
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be a boolean")
        if not isinstance(self.state, ExecutionState):
            raise TypeError("state must be an ExecutionState")
        _require_aware_utc(self.accepted_at, "accepted_at")
        if self.accepted and self.state is not ExecutionState.QUEUED:
            raise ValueError("accepted runtime state must be queued")

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class ExecutionStatusSnapshot:
    execution_id: UUID
    workflow_id: str
    state: ExecutionState
    progress: float
    updated_at: datetime
    current_stage: Optional[str] = None
    retry_count: int = 0
    worker_status: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    error_summary: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _require_uuid(self.execution_id, "execution_id")
        _require_non_empty(self.workflow_id, "workflow_id")
        if not isinstance(self.state, ExecutionState):
            raise TypeError("state must be an ExecutionState")
        if isinstance(self.progress, bool) or not isinstance(self.progress, (int, float)):
            raise TypeError("progress must be numeric")
        if not 0 <= self.progress <= 100:
            raise ValueError("progress must be between 0 and 100")
        if isinstance(self.retry_count, bool) or not isinstance(self.retry_count, int):
            raise TypeError("retry_count must be an integer")
        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        _require_aware_utc(self.updated_at, "updated_at")
        if self.estimated_completion is not None:
            _require_aware_utc(self.estimated_completion, "estimated_completion")
        if self.current_stage is not None and self.current_stage not in _ENGINE_STAGES:
            raise ValueError("current_stage must be an approved engine stage")
        _require_non_empty(self.contract_version, "contract_version")

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class ExecutionResultEnvelope:
    execution_id: UUID
    workflow_id: str
    terminal_state: ExecutionState
    result: Dict[str, Any]
    completed_at: datetime
    capability_summaries: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    result_version: str = "1.0.0"
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        _require_uuid(self.execution_id, "execution_id")
        _require_non_empty(self.workflow_id, "workflow_id")
        if not isinstance(self.terminal_state, ExecutionState):
            raise TypeError("terminal_state must be an ExecutionState")
        if self.terminal_state not in _TERMINAL_STATES:
            raise ValueError("terminal_state must be completed, failed, or cancelled")
        _require_aware_utc(self.completed_at, "completed_at")
        _require_non_empty(self.result_version, "result_version")
        _require_non_empty(self.contract_version, "contract_version")
        for field_name in ("result", "capability_summaries", "metrics", "errors"):
            _require_json_safe(getattr(self, field_name), field_name)

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)
