# app/engine/worker_manager.py
"""
Worker Manager - DOCUMENT 04 - PART 03
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum


logger = logging.getLogger(__name__)


class WorkerStatus(str, Enum):
    """Worker status."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class Worker:
    """Represents a worker."""
    worker_id: str
    status: WorkerStatus
    current_task_id: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: Optional[datetime] = None
    capacity: int = 1  # Max concurrent tasks
    current_load: int = 0


class WorkerManager:
    """
    Worker Manager - DOCUMENT 04 - Section 12
    
    Allocates workers, monitors workers,
    recovers failed workers, balances workload.
    """
    
    def __init__(self):
        self._workers: Dict[str, Worker] = {}
        self._max_workers = 10
    
    def register_worker(
        self,
        worker_id: str,
        capacity: int = 1,
    ) -> Worker:
        """Register a new worker."""
        worker = Worker(
            worker_id=worker_id,
            status=WorkerStatus.AVAILABLE,
            capacity=capacity,
        )
        self._workers[worker_id] = worker
        logger.info(f"✅ Worker registered: {worker_id}")
        return worker
    
    def get_available_worker(self) -> Optional[Worker]:
        """Get an available worker."""
        for worker in self._workers.values():
            if (worker.status == WorkerStatus.AVAILABLE and 
                worker.current_load < worker.capacity):
                return worker
        return None
    
    def assign_task(self, task_id: str, worker_id: str) -> bool:
        """Assign a task to a worker."""
        worker = self._workers.get(worker_id)
        if not worker:
            return False
        
        if worker.status != WorkerStatus.AVAILABLE:
            return False
        
        worker.status = WorkerStatus.BUSY
        worker.current_task_id = task_id
        worker.current_load += 1
        
        logger.info(f"📌 Task {task_id} assigned to worker {worker_id}")
        return True
    
    def complete_task(self, worker_id: str, success: bool) -> bool:
        """Complete a task."""
        worker = self._workers.get(worker_id)
        if not worker:
            return False
        
        if success:
            worker.tasks_completed += 1
        else:
            worker.tasks_failed += 1
        
        worker.current_task_id = None
        worker.current_load = max(0, worker.current_load - 1)
        worker.status = WorkerStatus.AVAILABLE
        
        logger.info(f"✅ Task completed on worker {worker_id}")
        return True
    
    def heartbeat(self, worker_id: str) -> bool:
        """Update worker heartbeat."""
        worker = self._workers.get(worker_id)
        if not worker:
            return False
        
        worker.last_heartbeat = datetime.now()
        return True
    
    def recover_failed_worker(self, worker_id: str) -> bool:
        """Recover a failed worker."""
        worker = self._workers.get(worker_id)
        if not worker:
            return False
        
        if worker.status == WorkerStatus.FAILED:
            worker.status = WorkerStatus.RECOVERING
            # Reset worker state
            worker.current_task_id = None
            worker.current_load = 0
            worker.status = WorkerStatus.AVAILABLE
            logger.info(f"🔄 Worker recovered: {worker_id}")
            return True
        
        return False
    
    def mark_worker_offline(self, worker_id: str) -> bool:
        """Mark a worker as offline."""
        worker = self._workers.get(worker_id)
        if not worker:
            return False
        
        worker.status = WorkerStatus.OFFLINE
        logger.info(f"⏹️ Worker offline: {worker_id}")
        return True
    
    def get_available_workers(self) -> List[Worker]:
        """Get all available workers."""
        return [
            w for w in self._workers.values()
            if w.status == WorkerStatus.AVAILABLE and w.current_load < w.capacity
        ]
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        total = len(self._workers)
        available = len(self.get_available_workers())
        busy = len([w for w in self._workers.values() if w.status == WorkerStatus.BUSY])
        offline = len([w for w in self._workers.values() if w.status == WorkerStatus.OFFLINE])
        failed = len([w for w in self._workers.values() if w.status == WorkerStatus.FAILED])
        
        total_completed = sum(w.tasks_completed for w in self._workers.values())
        total_failed = sum(w.tasks_failed for w in self._workers.values())
        
        return {
            "total": total,
            "available": available,
            "busy": busy,
            "offline": offline,
            "failed": failed,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "utilization": (busy / total * 100) if total > 0 else 0,
        }