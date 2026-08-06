# app/engine/execution_context.py
"""
Execution Context - DOCUMENT 04 - PART 04
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Optional, Dict, Any, List, Mapping
from uuid import UUID
import logging

from uuid_extensions import uuid7

from app.engine.enums import ExecutionState
from app.engine.workflow_engine import Workflow
from app.engine.lifecycle_manager import LifecycleManager
from app.engine.models import ExecutionCheckpoint, ExecutionProgress, ExecutionSnapshot


logger = logging.getLogger(__name__)


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
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("mapping keys must be strings")
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    raise TypeError(f"unsupported value type {type(value).__name__}")


@dataclass
class ExecutionContext:
    """
    Execution Context - Runtime context for an execution.
    """
    workflow_id: str
    workflow: Workflow
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    state: ExecutionState = ExecutionState.CREATED
    completed_task_ids: List[str] = field(default_factory=list)
    current_task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: Dict[str, int] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    execution_id: UUID = field(default_factory=uuid7)
    company_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    objective_type: Optional[str] = None
    analysis_type: Optional[str] = None
    material_codes: Optional[List[str]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    contract_version: str = "1.0.0"
    queued_at: Optional[datetime] = None
    current_stage: Optional[str] = None
    progress: float = 0.0

    def __post_init__(self):
        """Validate additive execution-contract fields."""
        if not isinstance(self.execution_id, UUID):
            raise TypeError("execution_id must be a UUID instance")
        for field_name in ("company_id", "user_id", "dataset_id"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, UUID):
                raise TypeError(f"{field_name} must be a UUID instance or None")
        if not isinstance(self.contract_version, str) or not self.contract_version.strip():
            raise ValueError("contract_version must be non-empty")
        if self.queued_at is not None and (
            self.queued_at.tzinfo is None or self.queued_at.utcoffset() is None
        ):
            raise ValueError("queued_at must be timezone-aware")
        if self.current_stage is not None and self.current_stage not in _ENGINE_STAGES:
            raise ValueError("current_stage must be an approved engine stage")
        if isinstance(self.progress, bool) or not isinstance(self.progress, (int, float)):
            raise TypeError("progress must be numeric")
        if not 0 <= self.progress <= 100:
            raise ValueError("progress must be between 0 and 100")
        _require_json_safe(self.params, "params")
        _require_json_safe(self.config, "config")
    
    def pause(self):
        """Pause execution."""
        if self.state is not ExecutionState.RUNNING:
            raise ValueError("execution can only be paused while running")
        self.state = ExecutionState.WAITING
        self.paused_at = datetime.now()
        logger.info(f"⏸️ Execution paused: {self.workflow_id}")
    
    def resume(self):
        """Resume execution."""
        if self.state is not ExecutionState.WAITING or self.paused_at is None:
            raise ValueError("execution can only be resumed from a paused waiting state")
        self.state = ExecutionState.RUNNING
        self.resumed_at = datetime.now()
        logger.info(f"▶️ Execution resumed: {self.workflow_id}")
    
    def complete(self):
        """Complete execution."""
        self.state = ExecutionState.COMPLETED
        self.completed_at = datetime.now()
        logger.info(f"✅ Execution completed: {self.workflow_id}")
    
    def fail(self, error: str):
        """Mark execution as failed."""
        self.state = ExecutionState.FAILED
        self.completed_at = datetime.now()
        self.errors.append({
            "error": error,
            "timestamp": datetime.now().isoformat(),
        })
        logger.error(f"❌ Execution failed: {self.workflow_id} - {error}")
    
    def cancel(self):
        """Cancel execution."""
        self.state = ExecutionState.CANCELLED
        self.completed_at = datetime.now()
        logger.info(f"⏹️ Execution cancelled: {self.workflow_id}")
    
    def add_completed_task(self, task_id: str):
        """Add a completed task."""
        if task_id not in self.completed_task_ids:
            self.completed_task_ids.append(task_id)
    
    def set_current_task(self, task_id: str):
        """Set current task."""
        self.current_task_id = task_id
    
    def increment_retry(self, task_id: str):
        """Increment retry count for a task."""
        if task_id not in self.retry_count:
            self.retry_count[task_id] = 0
        self.retry_count[task_id] += 1
    
    def get_retry_count(self, task_id: str) -> int:
        """Get retry count for a task."""
        return self.retry_count.get(task_id, 0)
    
    def add_error(self, error: str, context: Optional[Dict[str, Any]] = None):
        """Add an error."""
        self.errors.append({
            "error": error,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "resumed_at": self.resumed_at.isoformat() if self.resumed_at else None,
            "completed_task_ids": self.completed_task_ids,
            "current_task_id": self.current_task_id,
            "retry_count": self.retry_count,
            "error_count": len(self.errors),
            "last_error": self.errors[-1] if self.errors else None,
            "execution_id": str(self.execution_id),
            "company_id": str(self.company_id) if self.company_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "dataset_id": str(self.dataset_id) if self.dataset_id else None,
            "objective_type": self.objective_type,
            "analysis_type": self.analysis_type,
            "material_codes": list(self.material_codes) if self.material_codes else None,
            "params": _json_safe(self.params),
            "config": _json_safe(self.config),
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "contract_version": self.contract_version,
            "queued_at": _json_safe(self.queued_at) if self.queued_at else None,
            "current_stage": self.current_stage,
            "progress": self.progress,
        }


class ExecutionContextManager:
    """
    Context Manager for execution contexts.
    """
    
    def __init__(self):
        self._contexts: Dict[str, ExecutionContext] = {}
        self._contexts_by_execution_id: Dict[UUID, ExecutionContext] = {}
        self.lifecycle_manager = LifecycleManager()
    
    def create_context(
        self,
        workflow_id: str,
        workflow: Workflow,
    ) -> ExecutionContext:
        """Create a new execution context."""
        context = ExecutionContext(
            workflow_id=workflow_id,
            workflow=workflow,
        )
        self.register_context(context)
        return context

    def register_context(self, context: ExecutionContext) -> None:
        """Register one context under both workflow and execution identities."""
        if not isinstance(context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")
        if context.workflow_id in self._contexts:
            raise ValueError(f"workflow_id already registered: {context.workflow_id}")
        if context.execution_id in self._contexts_by_execution_id:
            raise ValueError(f"execution_id already registered: {context.execution_id}")
        self._contexts[context.workflow_id] = context
        self._contexts_by_execution_id[context.execution_id] = context
    
    def get_context(self, workflow_id: str) -> Optional[ExecutionContext]:
        """Get execution context."""
        return self._contexts.get(workflow_id)

    def get_context_by_execution_id(self, execution_id: UUID) -> Optional[ExecutionContext]:
        """Get execution context by its immutable execution identity."""
        return self._contexts_by_execution_id.get(execution_id)

    def remove_context(self, workflow_id: str) -> Optional[ExecutionContext]:
        """Remove a context from both in-memory indexes."""
        context = self._contexts.pop(workflow_id, None)
        if context is not None:
            self._contexts_by_execution_id.pop(context.execution_id, None)
        return context
    
    def update_context(self, context: ExecutionContext):
        """Update execution context."""
        self._contexts[context.workflow_id] = context
    
    def start_execution(self, workflow_id: str) -> bool:
        """Start execution."""
        context = self.get_context(workflow_id)
        if not context:
            return False
        
        context.state = ExecutionState.RUNNING
        context.started_at = datetime.now()
        
        # Create initial checkpoint
        self.lifecycle_manager.create_checkpoint(
            workflow_id=workflow_id,
            state=ExecutionState.RUNNING,
            completed_task_ids=context.completed_task_ids,
        )
        
        return True
    
    def pause_execution(self, workflow_id: str) -> bool:
        """Pause execution."""
        context = self.get_context(workflow_id)
        if not context:
            return False
        
        context.pause()
        self.lifecycle_manager.create_checkpoint(
            workflow_id=workflow_id,
            state=ExecutionState.WAITING,
            completed_task_ids=list(context.completed_task_ids),
            current_task_id=context.current_task_id,
        )
        return True
    
    def resume_execution(self, workflow_id: str) -> bool:
        """Resume execution."""
        context = self.get_context(workflow_id)
        if not context:
            return False
        if context.state is not ExecutionState.WAITING or context.paused_at is None:
            raise ValueError("execution can only be resumed from a paused waiting state")
        
        # Check if we have a checkpoint to resume from
        checkpoint = self.lifecycle_manager.resume_from_checkpoint(workflow_id)
        if checkpoint:
            context.completed_task_ids = checkpoint.completed_task_ids
            context.current_task_id = checkpoint.current_task_id
        
        context.resume()
        return True
    
    def complete_execution(self, workflow_id: str) -> bool:
        """Complete execution."""
        context = self.get_context(workflow_id)
        if not context:
            return False
        
        context.complete()
        
        # Final checkpoint
        self.lifecycle_manager.create_checkpoint(
            workflow_id=workflow_id,
            state=ExecutionState.COMPLETED,
            completed_task_ids=context.completed_task_ids,
        )
        
        return True
