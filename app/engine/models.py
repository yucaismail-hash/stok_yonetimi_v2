# app/engine/models.py
"""
Execution Lifecycle Models
DOCUMENT 04 - PART 04
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from app.engine.enums import ExecutionState, TaskStatus


@dataclass
class ExecutionCheckpoint:
    """Execution checkpoint for resume."""
    checkpoint_id: str
    workflow_id: str
    state: ExecutionState
    completed_task_ids: List[str]
    current_task_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionProgress:
    """Execution progress information."""
    completed_tasks: int = 0
    remaining_tasks: int = 0
    completed_skus: int = 0
    remaining_skus: int = 0
    current_task: Optional[str] = None
    current_worker: Optional[str] = None
    progress_percentage: float = 0.0
    estimated_remaining_seconds: Optional[float] = None
    elapsed_seconds: float = 0.0


@dataclass
class ExecutionMetrics:
    """Execution metrics."""
    execution_duration_ms: Optional[float] = None
    cpu_time_ms: Optional[float] = None
    ram_usage_mb: Optional[float] = None
    peak_ram_mb: Optional[float] = None
    queue_time_ms: Optional[float] = None
    worker_count: int = 0
    task_count: int = 0
    sku_count: int = 0
    execution_cost: float = 0.0
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionSnapshot:
    """Full execution snapshot for user visibility."""
    workflow_id: str
    status: ExecutionState
    current_task: Optional[str] = None
    completed_tasks: int = 0
    total_tasks: int = 0
    progress_percentage: float = 0.0
    estimated_remaining_seconds: Optional[float] = None
    elapsed_seconds: float = 0.0
    warnings: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None