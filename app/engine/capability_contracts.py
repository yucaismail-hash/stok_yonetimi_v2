"""Frozen, versioned contracts for one capability execution attempt."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID

from app.engine.capability_registry import Capability
from app.engine.enums import TaskStatus


_SENSITIVE_DETAIL_KEYS = {"password", "credential", "secret", "token", "authorization", "dataset_rows", "personal_information"}


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def _require_aware_utc(value: datetime, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{name} must be UTC")


def _json_safe(value: Any) -> Any:
    if isinstance(value, CapabilityExecutionError):
        return value.to_dict()
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
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        return { _json_key(key): _json_safe(item) for key, item in value.items() }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    raise TypeError(f"unsupported value type {type(value).__name__}")


def _json_key(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("mapping keys must be strings")
    return value


def _require_json_safe(value: Any, name: str) -> None:
    try:
        _json_safe(value)
    except (TypeError, ValueError) as exc:
        raise type(exc)(f"{name} must be JSON-safe: {exc}") from exc


def _require_non_sensitive_details(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str) and any(term in key.casefold() for term in _SENSITIVE_DETAIL_KEYS):
                raise ValueError("details must not contain sensitive values")
            _require_non_sensitive_details(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _require_non_sensitive_details(item)


@dataclass(frozen=True)
class CapabilityExecutionError:
    code: str
    message: str
    category: str
    retryable: bool
    occurred_at: datetime
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("code", "message", "category"):
            _require_non_empty(getattr(self, name), name)
        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be a bool")
        _require_aware_utc(self.occurred_at, "occurred_at")
        _require_json_safe(self.details, "details")
        _require_non_sensitive_details(self.details)

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class CapabilityExecutionRequest:
    execution_id: UUID
    workflow_id: str
    task_id: str
    capability: Capability
    company_id: UUID
    user_id: UUID
    dataset_id: UUID
    timeout_seconds: int
    material_codes: Optional[List[str]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    upstream_results: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    attempt: int = 1
    contract_version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        for name in ("execution_id", "company_id", "user_id", "dataset_id"):
            if not isinstance(getattr(self, name), UUID):
                raise TypeError(f"{name} must be a UUID instance")
        for name in ("workflow_id", "task_id", "contract_version"):
            _require_non_empty(getattr(self, name), name)
        if not isinstance(self.capability, Capability):
            raise TypeError("capability must be a Capability")
        if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError("attempt must be at least 1")
        _require_aware_utc(self.created_at, "created_at")
        if self.material_codes is not None:
            if not isinstance(self.material_codes, list) or not all(isinstance(code, str) for code in self.material_codes):
                raise TypeError("material_codes must be a list of strings or None")
            object.__setattr__(self, "material_codes", list(self.material_codes))
        _require_json_safe(self.params, "params")
        _require_json_safe(self.upstream_results, "upstream_results")

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class CapabilityExecutionResult:
    execution_id: UUID
    workflow_id: str
    task_id: str
    capability: Capability
    state: TaskStatus
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    attempt: int
    result: Dict[str, Any] = field(default_factory=dict)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[CapabilityExecutionError] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    result_version: str = "1.0.0"
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, UUID):
            raise TypeError("execution_id must be a UUID instance")
        for name in ("workflow_id", "task_id", "result_version", "contract_version"):
            _require_non_empty(getattr(self, name), name)
        if not isinstance(self.capability, Capability):
            raise TypeError("capability must be a Capability")
        if self.state not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            raise ValueError("state must be completed or failed")
        _require_aware_utc(self.started_at, "started_at")
        _require_aware_utc(self.completed_at, "completed_at")
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        if isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, (int, float)) or self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError("attempt must be at least 1")
        if not isinstance(self.errors, list) or not all(isinstance(error, CapabilityExecutionError) for error in self.errors):
            raise TypeError("errors must be CapabilityExecutionError values")
        if self.state is TaskStatus.COMPLETED and self.errors:
            raise ValueError("completed results must not contain errors")
        if self.state is TaskStatus.FAILED and not self.errors:
            raise ValueError("failed results must contain an error")
        for name in ("result", "warnings", "metrics"):
            _require_json_safe(getattr(self, name), name)

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(self.__dict__)
