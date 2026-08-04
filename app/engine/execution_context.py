# app/engine/execution_context.py
"""
Execution Context - DOCUMENT 04 - PART 04
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from app.engine.enums import ExecutionState
from app.engine.workflow_engine import Workflow
from app.engine.lifecycle_manager import LifecycleManager
from app.engine.models import ExecutionCheckpoint, ExecutionProgress, ExecutionSnapshot


logger = logging.getLogger(__name__)


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
    
    def pause(self):
        """Pause execution."""
        self.state = ExecutionState.PAUSED
        self.paused_at = datetime.now()
        logger.info(f"⏸️ Execution paused: {self.workflow_id}")
    
    def resume(self):
        """Resume execution."""
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
        }


class ExecutionContextManager:
    """
    Context Manager for execution contexts.
    """
    
    def __init__(self):
        self._contexts: Dict[str, ExecutionContext] = {}
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
        self._contexts[workflow_id] = context
        return context
    
    def get_context(self, workflow_id: str) -> Optional[ExecutionContext]:
        """Get execution context."""
        return self._contexts.get(workflow_id)
    
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
        return True
    
    def resume_execution(self, workflow_id: str) -> bool:
        """Resume execution."""
        context = self.get_context(workflow_id)
        if not context:
            return False
        
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