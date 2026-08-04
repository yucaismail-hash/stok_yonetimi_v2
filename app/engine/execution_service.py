# app/engine/execution_service.py
"""
Execution Service - DOCUMENT 04 - PART 04
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.engine.enums import ExecutionState
from app.engine.workflow_engine import Workflow, Task
from app.engine.lifecycle_manager import LifecycleManager
from app.engine.execution_context import ExecutionContext, ExecutionContextManager
from app.engine.models import ExecutionCheckpoint, ExecutionProgress, ExecutionSnapshot


logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Execution Service - DOCUMENT 04 - PART 04
    
    Main service for execution lifecycle management.
    """
    
    def __init__(self):
        self.context_manager = ExecutionContextManager()
        self.lifecycle_manager = LifecycleManager()
    
    def create_execution(
        self,
        workflow_id: str,
        workflow: Workflow,
    ) -> ExecutionContext:
        """Create a new execution."""
        return self.context_manager.create_context(workflow_id, workflow)
    
    def start_execution(self, workflow_id: str) -> bool:
        """Start execution."""
        return self.context_manager.start_execution(workflow_id)
    
    def pause_execution(self, workflow_id: str) -> bool:
        """Pause execution."""
        return self.context_manager.pause_execution(workflow_id)
    
    def resume_execution(self, workflow_id: str) -> bool:
        """Resume execution."""
        return self.context_manager.resume_execution(workflow_id)
    
    def complete_execution(self, workflow_id: str) -> bool:
        """Complete execution."""
        return self.context_manager.complete_execution(workflow_id)
    
    def cancel_execution(self, workflow_id: str) -> bool:
        """Cancel execution."""
        context = self.context_manager.get_context(workflow_id)
        if not context:
            return False
        context.cancel()
        return True
    
    def get_progress(self, workflow_id: str) -> Optional[ExecutionProgress]:
        """Get execution progress."""
        context = self.context_manager.get_context(workflow_id)
        if not context:
            return None
        
        total_tasks = len(context.workflow.tasks)
        completed_count = len(context.completed_task_ids)
        remaining_count = total_tasks - completed_count
        
        progress_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return ExecutionProgress(
            completed_tasks=completed_count,
            remaining_tasks=remaining_count,
            progress_percentage=round(progress_percentage, 2),
            current_task=context.current_task_id,
        )
    
    def get_snapshot(self, workflow_id: str) -> Optional[ExecutionSnapshot]:
        """Get execution snapshot for user visibility."""
        context = self.context_manager.get_context(workflow_id)
        if not context:
            return None
        
        progress = self.get_progress(workflow_id)
        if not progress:
            return None
        
        return ExecutionSnapshot(
            workflow_id=workflow_id,
            status=context.state,
            current_task=context.current_task_id,
            completed_tasks=progress.completed_tasks,
            total_tasks=progress.completed_tasks + progress.remaining_tasks,
            progress_percentage=progress.progress_percentage,
            warnings=[],
            failures=[e["error"] for e in context.errors],
            created_at=context.created_at,
            updated_at=datetime.now(),
            completed_at=context.completed_at,
        )
    
    def get_checkpoints(self, workflow_id: str) -> List[ExecutionCheckpoint]:
        """Get all checkpoints for a workflow."""
        return self.lifecycle_manager._checkpoints.get(workflow_id, [])
    
    def get_metrics(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get execution metrics."""
        metrics = self.lifecycle_manager.get_metrics(workflow_id)
        if metrics:
            return {
                "execution_duration_ms": metrics.execution_duration_ms,
                "cpu_time_ms": metrics.cpu_time_ms,
                "ram_usage_mb": metrics.ram_usage_mb,
                "peak_ram_mb": metrics.peak_ram_mb,
                "queue_time_ms": metrics.queue_time_ms,
                "worker_count": metrics.worker_count,
                "task_count": metrics.task_count,
                "sku_count": metrics.sku_count,
                "execution_cost": metrics.execution_cost,
                "collected_at": metrics.collected_at.isoformat(),
            }
        return None
    
    def list_executions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all executions for a user."""
        # Placeholder - actual implementation will query database
        executions = []
        for workflow_id, context in self.context_manager._contexts.items():
            snapshot = self.get_snapshot(workflow_id)
            if snapshot:
                executions.append({
                    "workflow_id": workflow_id,
                    "status": snapshot.status.value,
                    "progress": snapshot.progress_percentage,
                    "created_at": snapshot.created_at.isoformat(),
                    "updated_at": snapshot.updated_at.isoformat(),
                })
        return executions