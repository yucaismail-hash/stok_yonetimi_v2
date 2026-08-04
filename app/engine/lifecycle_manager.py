# app/engine/lifecycle_manager.py
"""
Execution Lifecycle Manager
DOCUMENT 04 - PART 04
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from uuid import uuid4

from app.engine.enums import ExecutionState, TaskStatus
from app.engine.models import (
    ExecutionCheckpoint,
    ExecutionProgress,
    ExecutionMetrics,
    ExecutionSnapshot,
)
from app.engine.workflow_engine import Workflow, Task


logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Lifecycle Manager - DOCUMENT 04 - PART 04
    
    Manages execution lifecycle, state transitions,
    checkpoints, progress tracking, and metrics.
    """
    
    def __init__(self):
        self._checkpoints: Dict[str, List[ExecutionCheckpoint]] = {}
        self._metrics: Dict[str, ExecutionMetrics] = {}
        self._snapshots: Dict[str, ExecutionSnapshot] = {}
    
    def create_checkpoint(
        self,
        workflow_id: str,
        state: ExecutionState,
        completed_task_ids: List[str],
        current_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCheckpoint:
        """Create an execution checkpoint."""
        checkpoint = ExecutionCheckpoint(
            checkpoint_id=str(uuid4()),
            workflow_id=workflow_id,
            state=state,
            completed_task_ids=completed_task_ids,
            current_task_id=current_task_id,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        
        if workflow_id not in self._checkpoints:
            self._checkpoints[workflow_id] = []
        self._checkpoints[workflow_id].append(checkpoint)
        
        logger.info(f"📌 Checkpoint created: {checkpoint.checkpoint_id}")
        
        return checkpoint
    
    def get_latest_checkpoint(self, workflow_id: str) -> Optional[ExecutionCheckpoint]:
        """Get the latest checkpoint for a workflow."""
        checkpoints = self._checkpoints.get(workflow_id, [])
        if checkpoints:
            return checkpoints[-1]
        return None
    
    def resume_from_checkpoint(self, workflow_id: str) -> Optional[ExecutionCheckpoint]:
        """Resume execution from the latest checkpoint."""
        checkpoint = self.get_latest_checkpoint(workflow_id)
        if checkpoint:
            logger.info(f"🔄 Resuming from checkpoint: {checkpoint.checkpoint_id}")
        return checkpoint
    
    def calculate_progress(
        self,
        workflow: Workflow,
        completed_tasks: List[str],
    ) -> ExecutionProgress:
        """Calculate execution progress."""
        total_tasks = len(workflow.tasks)
        completed_count = len(completed_tasks)
        remaining_count = total_tasks - completed_count
        
        progress_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return ExecutionProgress(
            completed_tasks=completed_count,
            remaining_tasks=remaining_count,
            progress_percentage=round(progress_percentage, 2),
        )
    
    def update_snapshot(
        self,
        workflow_id: str,
        status: ExecutionState,
        progress: ExecutionProgress,
        current_task: Optional[str] = None,
        warnings: Optional[List[str]] = None,
        failures: Optional[List[str]] = None,
    ) -> ExecutionSnapshot:
        """Update execution snapshot for user visibility."""
        existing = self._snapshots.get(workflow_id)
        
        snapshot = ExecutionSnapshot(
            workflow_id=workflow_id,
            status=status,
            current_task=current_task or (existing.current_task if existing else None),
            completed_tasks=progress.completed_tasks,
            total_tasks=progress.completed_tasks + progress.remaining_tasks,
            progress_percentage=progress.progress_percentage,
            estimated_remaining_seconds=progress.estimated_remaining_seconds,
            elapsed_seconds=progress.elapsed_seconds,
            warnings=warnings or (existing.warnings if existing else []),
            failures=failures or (existing.failures if existing else []),
            updated_at=datetime.now(),
        )
        
        if status == ExecutionState.COMPLETED:
            snapshot.completed_at = datetime.now()
        
        self._snapshots[workflow_id] = snapshot
        
        return snapshot
    
    def get_snapshot(self, workflow_id: str) -> Optional[ExecutionSnapshot]:
        """Get execution snapshot for user visibility."""
        return self._snapshots.get(workflow_id)
    
    def record_metrics(
        self,
        workflow_id: str,
        duration_ms: Optional[float] = None,
        cpu_time_ms: Optional[float] = None,
        ram_usage_mb: Optional[float] = None,
        peak_ram_mb: Optional[float] = None,
        queue_time_ms: Optional[float] = None,
        worker_count: int = 0,
        task_count: int = 0,
        sku_count: int = 0,
        execution_cost: float = 0.0,
    ) -> ExecutionMetrics:
        """Record execution metrics."""
        metrics = ExecutionMetrics(
            execution_duration_ms=duration_ms,
            cpu_time_ms=cpu_time_ms,
            ram_usage_mb=ram_usage_mb,
            peak_ram_mb=peak_ram_mb,
            queue_time_ms=queue_time_ms,
            worker_count=worker_count,
            task_count=task_count,
            sku_count=sku_count,
            execution_cost=execution_cost,
            collected_at=datetime.now(),
        )
        
        self._metrics[workflow_id] = metrics
        
        logger.info(f"📊 Metrics recorded for workflow: {workflow_id}")
        
        return metrics
    
    def get_metrics(self, workflow_id: str) -> Optional[ExecutionMetrics]:
        """Get execution metrics."""
        return self._metrics.get(workflow_id)
    
    def calculate_eta(
        self,
        workflow: Workflow,
        progress: ExecutionProgress,
        elapsed_seconds: float,
    ) -> Optional[float]:
        """
        Calculate estimated remaining time.
        DOCUMENT 04 - Section 6: Estimated Time
        """
        if progress.progress_percentage == 0:
            return None
        
        # Simple linear extrapolation
        remaining_percentage = 100 - progress.progress_percentage
        elapsed_percentage = progress.progress_percentage
        
        if elapsed_percentage > 0:
            estimated_total = (elapsed_seconds / elapsed_percentage) * 100
            estimated_remaining = estimated_total - elapsed_seconds
            return max(0, estimated_remaining)
        
        return None