"""Pure user-facing execution-notification contract."""

from dataclasses import dataclass
from math import isfinite
from typing import Any, Dict, Optional


_RETRY_STATUSES = {"not_applicable", "manual_action_required", "automatic_retry_possible", "automatic_retry_scheduled", "no_retry", "support_review_required"}
_SEVERITIES = {"info", "warning", "error"}
_FORBIDDEN = {"motor", "engine", "executor", "worker", "adapter", "protocol", "implementation", "json-safe", "queue", "traceback"}


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and isfinite(value):
        return value
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    raise TypeError("notice values must be JSON-safe")


@dataclass(frozen=True)
class UserExecutionNotice:
    title: str
    message: str
    user_action: str
    system_action: str
    retry_status: str
    completed_work_preserved: bool
    notice_code: str
    severity: str
    support_reference: Optional[str] = None
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name in ("title", "message", "user_action", "system_action", "notice_code", "severity", "contract_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.retry_status not in _RETRY_STATUSES:
            raise ValueError("retry_status is not approved")
        if self.severity not in _SEVERITIES:
            raise ValueError("severity is not approved")
        if not isinstance(self.completed_work_preserved, bool):
            raise TypeError("completed_work_preserved must be a bool")
        for name in ("title", "message", "user_action", "system_action"):
            lowered = getattr(self, name).casefold()
            if any(term in lowered for term in _FORBIDDEN):
                raise ValueError(f"{name} contains forbidden internal terminology")
        if self.support_reference is not None and (not isinstance(self.support_reference, str) or not self.support_reference.strip()):
            raise ValueError("support_reference must be non-empty when supplied")

    def to_dict(self) -> Dict[str, Any]:
        return _safe(self.__dict__)
