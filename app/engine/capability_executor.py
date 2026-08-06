"""Injected boundary for one deterministic capability attempt.

This module deliberately has no production defaults or runtime wiring.
"""

import inspect
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from app.engine.capability_contracts import (
    CapabilityExecutionError,
    CapabilityExecutionRequest,
    CapabilityExecutionResult,
    _require_json_safe,
)
from app.engine.enums import TaskStatus


class CapabilityExecutorError(RuntimeError):
    code = "EXECUTOR_ERROR"


class ExecutorNotConfiguredError(CapabilityExecutorError):
    code = "EXECUTOR_NOT_CONFIGURED"


class CapabilityImplementationNotFoundError(CapabilityExecutorError):
    code = "IMPLEMENTATION_NOT_FOUND"


class ResolverProtocolError(CapabilityExecutorError):
    code = "RESOLVER_PROTOCOL_VIOLATION"


class ProviderProtocolError(CapabilityExecutorError):
    code = "PROVIDER_PROTOCOL_VIOLATION"


class AdapterProtocolError(CapabilityExecutorError):
    code = "ADAPTER_PROTOCOL_VIOLATION"


class CapabilityInputValidationError(ValueError):
    """Adapter signal for validated-but-rejected capability input."""


class DatasetInputUnavailableError(RuntimeError):
    """Adapter signal for temporarily unavailable dataset input after start."""


class CapabilityExecutor:
    """Runs only injected doubles/adapters; it never persists or schedules work."""

    def __init__(
        self,
        implementation_resolver: Optional[Callable[..., Any]] = None,
        input_provider: Optional[Callable[..., Any]] = None,
        implementation_adapter: Optional[Callable[..., Any]] = None,
        timeout_runner: Optional[Callable[..., Any]] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self._implementation_resolver = implementation_resolver
        self._input_provider = input_provider
        self._implementation_adapter = implementation_adapter
        self._timeout_runner = timeout_runner
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def execute(self, request: CapabilityExecutionRequest) -> CapabilityExecutionResult:
        if not isinstance(request, CapabilityExecutionRequest):
            raise TypeError("request must be a CapabilityExecutionRequest")
        if any(value is None for value in (self._implementation_resolver, self._input_provider, self._implementation_adapter, self._timeout_runner)):
            raise ExecutorNotConfiguredError("executor dependencies are not configured")
        implementation = await self._call(self._implementation_resolver, request.capability)
        if implementation is None:
            raise CapabilityImplementationNotFoundError("capability implementation was not found")
        if not callable(self._input_provider):
            raise ProviderProtocolError("input provider is not callable")
        prepared_input = await self._call(self._input_provider, request)
        if prepared_input is None:
            raise ProviderProtocolError("input provider returned no prepared input")
        if not callable(self._implementation_adapter):
            raise AdapterProtocolError("implementation adapter is not callable")
        if not callable(self._timeout_runner):
            raise AdapterProtocolError("timeout runner is not callable")
        started_at = self._now()
        try:
            async def invoke() -> Any:
                return await self._call(self._implementation_adapter, implementation, prepared_input, request)

            raw_result = await self._call(self._timeout_runner, invoke, request.timeout_seconds)
        except CapabilityInputValidationError as exc:
            return self._failed(request, started_at, "CAPABILITY_INPUT_INVALID", "capability input was rejected", "input_validation", False, {"reason": str(exc)})
        except DatasetInputUnavailableError as exc:
            return self._failed(request, started_at, "DATASET_INPUT_UNAVAILABLE", "dataset input was temporarily unavailable", "dataset_input", True, {"reason": str(exc)})
        except TimeoutError:
            return self._failed(request, started_at, "CAPABILITY_TIMEOUT", "capability invocation exceeded its time limit", "timeout", True)
        except Exception as exc:
            return self._failed(request, started_at, "CAPABILITY_EXECUTION_FAILED", "capability invocation failed", "execution", False, {"exception_type": type(exc).__name__})
        try:
            if not isinstance(raw_result, dict):
                raise ValueError("capability result must be a mapping")
            _require_json_safe(raw_result, "result")
        except (TypeError, ValueError) as exc:
            return self._failed(request, started_at, "INVALID_CAPABILITY_RESULT", "capability result could not be validated", "result_validation", False, {"reason": str(exc)})
        completed_at = self._now()
        return CapabilityExecutionResult(request.execution_id, request.workflow_id, request.task_id, request.capability, TaskStatus.COMPLETED, started_at, completed_at, self._duration(started_at, completed_at), request.attempt, result=raw_result)

    async def _call(self, callback: Callable[..., Any], *args: Any) -> Any:
        if not callable(callback):
            raise ResolverProtocolError("resolver is not callable")
        value = callback(*args)
        if inspect.isawaitable(value):
            return await value
        return value

    def _now(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise RuntimeError("clock must return an aware UTC datetime")
        return value

    def _failed(self, request: CapabilityExecutionRequest, started_at: datetime, code: str, message: str, category: str, retryable: bool, details: Optional[dict] = None) -> CapabilityExecutionResult:
        completed_at = self._now()
        error = CapabilityExecutionError(code, message, category, retryable, completed_at, details or {})
        return CapabilityExecutionResult(request.execution_id, request.workflow_id, request.task_id, request.capability, TaskStatus.FAILED, started_at, completed_at, self._duration(started_at, completed_at), request.attempt, errors=[error])

    @staticmethod
    def _duration(started_at: datetime, completed_at: datetime) -> float:
        return max(0.0, (completed_at - started_at).total_seconds() * 1000)
