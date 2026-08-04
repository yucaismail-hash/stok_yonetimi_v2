# app/engine/task_scheduler.py
"""
Task Scheduler - DOCUMENT 04 - PART 03
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.engine.enums import TaskType, TaskPriority, TaskStatus
from app.engine.workflow_engine import Workflow, Task
from app.engine.workflow_generator import WorkflowGenerator
from app.engine.execution_policy import default_execution_policy


logger = logging.getLogger(__name__)


class ExecutionPolicy(str, Enum):
    """DOCUMENT 04 - Section 13: Execution Policies"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    DEFERRED = "deferred"
    RETRY = "retry"


@dataclass
class ScheduledTask:
    """A task with scheduling information."""
    task: Task
    scheduled_order: int
    assigned_worker: Optional[str] = None
    estimated_start: Optional[float] = None
    estimated_end: Optional[float] = None
    policy: ExecutionPolicy = ExecutionPolicy.SEQUENTIAL


@dataclass
class ExecutionPlan:
    """Complete execution plan."""
    workflow_id: str
    tasks: List[ScheduledTask]
    execution_order: List[str]  # Task IDs in execution order
    parallel_groups: List[List[str]]  # Groups of tasks that can run in parallel
    total_estimated_duration: float
    max_parallel_tasks: int


class TaskScheduler:
    """
    Task Scheduler - DOCUMENT 04 - Section 10
    
    Receives optimized execution graph.
    Assigns workers, determines execution order,
    detects parallel tasks, manages priorities.
    """
    
    def __init__(self, max_parallel_tasks: int = 4):
        self.max_parallel_tasks = max_parallel_tasks
        self.generator = WorkflowGenerator()
    
    def schedule(
        self,
        workflow: Workflow,
        available_workers: Optional[List[str]] = None,
        resource_limits: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """
        Schedule tasks for execution.
        """
        workers = available_workers or ["worker-1", "worker-2", "worker-3", "worker-4"]
        resource_limits = resource_limits or {
            "max_parallel": self.max_parallel_tasks,
            "cpu_per_task": 1,
            "memory_per_task": 512,
        }
        
        # 1. Get execution order
        execution_order = self.generator.get_execution_order(workflow)
        
        # 2. Detect parallel groups
        parallel_groups = self._detect_parallel_groups(execution_order)
        
        # 3. Assign workers
        scheduled_tasks = []
        worker_idx = 0
        
        for order_idx, task in enumerate(execution_order):
            # Check if task can be parallelized
            policy = self._determine_policy(task, parallel_groups)
            
            # Assign worker
            if policy == ExecutionPolicy.PARALLEL:
                assigned_worker = workers[worker_idx % len(workers)]
                worker_idx += 1
            else:
                assigned_worker = workers[0]
            
            scheduled_task = ScheduledTask(
                task=task,
                scheduled_order=order_idx,
                assigned_worker=assigned_worker,
                policy=policy,
            )
            scheduled_tasks.append(scheduled_task)
        
        # 4. Calculate estimated duration
        total_duration = sum(
            t.task.timeout_seconds / 2 for t in execution_order
        )
        
        return ExecutionPlan(
            workflow_id=workflow.workflow_id,
            tasks=scheduled_tasks,
            execution_order=[t.task_id for t in execution_order],
            parallel_groups=parallel_groups,
            total_estimated_duration=total_duration,
            max_parallel_tasks=len(parallel_groups) if parallel_groups else 1,
        )
    
    def _detect_parallel_groups(self, tasks: List[Task]) -> List[List[str]]:
        """
        Detect tasks that can run in parallel.
        DOCUMENT 04 - Section 11: Parallel Execution
        """
        groups = []
        processed = set()
        
        for i, task in enumerate(tasks):
            if task.task_id in processed:
                continue
            
            # Check if task can run parallel with others
            can_parallel = []
            for j, other in enumerate(tasks[i+1:], i+1):
                if other.task_id in processed:
                    continue
                
                # Check if they have dependencies on each other
                if self._can_run_parallel(task, other):
                    can_parallel.append(other.task_id)
                    processed.add(other.task_id)
            
            if can_parallel:
                group = [task.task_id] + can_parallel
                groups.append(group)
                processed.add(task.task_id)
            else:
                groups.append([task.task_id])
                processed.add(task.task_id)
        
        return groups
    
    def _can_run_parallel(self, task1: Task, task2: Task) -> bool:
        """Check if two tasks can run in parallel."""
        # Check if they depend on each other
        if task2.task_type in task1.depends_on:
            return False
        if task1.task_type in task2.depends_on:
            return False
        
        # Check if they share dependencies
        shared_deps = set(task1.depends_on) & set(task2.depends_on)
        if shared_deps:
            # They can still run parallel if dependencies are met
            return True
        
        # Different task types can usually run parallel
        return task1.task_type != task2.task_type
    
    def _determine_policy(
        self,
        task: Task,
        parallel_groups: List[List[str]],
    ) -> ExecutionPolicy:
        """Determine execution policy for a task."""
        # Check if task is in a parallel group
        for group in parallel_groups:
            if task.task_id in group and len(group) > 1:
                return ExecutionPolicy.PARALLEL
        
        # Check dependencies
        if task.depends_on:
            return ExecutionPolicy.SEQUENTIAL
        
        # Default
        return ExecutionPolicy.SEQUENTIAL
    def __init__(self):
        self.policy = default_execution_policy
        self.max_parallel_tasks = self.policy.parallel_config.max_parallel_tasks
    
    def get_retry_count(self, task_type: str) -> int:
        """Get retry count from policy."""
        return self.policy.get_task_retry_count(task_type)
    
    def get_timeout(self, task_type: str) -> int:
        """Get timeout from policy."""
        return self.policy.get_task_timeout(task_type)