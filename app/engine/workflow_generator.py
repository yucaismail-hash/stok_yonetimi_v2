# app/engine/workflow_generator.py
"""
Workflow Generator
DOCUMENT 04 - Section 7 & 8
"""

from typing import List, Dict, Any, Optional, Set
from uuid import uuid4
from datetime import datetime
import logging

from app.engine.enums import (
    BusinessObjective,
    TaskType,
    ExecutionState,
    TaskPriority,
    TaskStatus,
)
from app.engine.business_objectives import (
    BusinessObjectiveDefinition,
    WorkflowStep,
    get_objective,
    OBJECTIVE_REGISTRY,
)

logger = logging.getLogger(__name__)


class Workflow:
    """Represents a workflow execution."""
    
    def __init__(
        self,
        workflow_id: str,
        objective_type: BusinessObjective,
        dataset_id: str,
        user_id: str,
        company_id: str,
        params: Optional[Dict[str, Any]] = None,
    ):
        self.workflow_id = workflow_id
        self.objective_type = objective_type
        self.dataset_id = dataset_id
        self.user_id = user_id
        self.company_id = company_id
        self.params = params or {}
        self.state = ExecutionState.CREATED
        self.tasks: List[Task] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
    
    def add_task(self, task: 'Task'):
        """Add a task to the workflow."""
        self.tasks.append(task)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "objective_type": self.objective_type.value,
            "dataset_id": self.dataset_id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "state": self.state.value,
            "params": self.params,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


class Task:
    """Represents a single task within a workflow."""
    
    def __init__(
        self,
        task_id: str,
        task_type: TaskType,
        order: int,
        depends_on: List[TaskType],
        is_functional: bool = True,
        can_skip: bool = False,
        priority: TaskPriority = TaskPriority.MEDIUM,
        retry_count: int = 3,
        timeout_seconds: int = 300,
        params: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.order = order
        self.depends_on = depends_on
        self.is_functional = is_functional
        self.can_skip = can_skip
        self.priority = priority
        self.retry_count = retry_count
        self.timeout_seconds = timeout_seconds
        self.params = params or {}
        self.status = TaskStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "order": self.order,
            "depends_on": [t.value for t in self.depends_on],
            "is_functional": self.is_functional,
            "can_skip": self.can_skip,
            "priority": self.priority.value,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
        }


class WorkflowGenerator:
    """
    Workflow Generator - DOCUMENT 04 Section 7 & 8
    
    Generates workflows from business objectives.
    """
    
    def __init__(self):
        self.objective_registry = OBJECTIVE_REGISTRY
    
    def generate(
        self,
        objective_type: BusinessObjective,
        dataset_id: str,
        user_id: str,
        company_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Generate a workflow from a business objective.
        """
        # 1. Get objective definition
        objective = get_objective(objective_type)
        if not objective:
            raise ValueError(f"Unknown objective type: {objective_type}")
        
        # 2. Create workflow
        workflow_id = str(uuid4())
        workflow = Workflow(
            workflow_id=workflow_id,
            objective_type=objective_type,
            dataset_id=dataset_id,
            user_id=user_id,
            company_id=company_id,
            params=params,
        )
        
        # 3. Generate tasks from steps
        for order, step in enumerate(objective.steps):
            task = self._create_task(step, order)
            workflow.add_task(task)
        
        # 4. Validate workflow
        self._validate_workflow(workflow)
        
        workflow.state = ExecutionState.CREATED
        
        logger.info(f"✅ Workflow generated: {workflow_id} for {objective_type.value}")
        
        return workflow
    
    def _create_task(self, step: WorkflowStep, order: int) -> Task:
        """Create a task from a workflow step."""
        task_id = str(uuid4())
        return Task(
            task_id=task_id,
            task_type=step.task_type,
            order=order,
            depends_on=step.depends_on,
            is_functional=step.is_functional,
            can_skip=step.can_skip,
            priority=step.priority,
            retry_count=step.retry_count,
            timeout_seconds=step.timeout_seconds,
        )
    
    def _validate_workflow(self, workflow: Workflow):
        """Validate workflow dependencies."""
        task_types = {t.task_type for t in workflow.tasks}
        
        for task in workflow.tasks:
            for dep in task.depends_on:
                if dep not in task_types:
                    raise ValueError(
                        f"Task {task.task_type.value} depends on {dep.value} "
                        f"which is not in the workflow"
                    )
        
        # Check for circular dependencies
        self._check_circular_dependencies(workflow.tasks)
    
    def _check_circular_dependencies(self, tasks: List[Task]):
        """Check for circular dependencies."""
        visited = set()
        rec_stack = set()
        
        task_map = {t.task_type: t for t in tasks}
        
        def dfs(task_type: TaskType) -> bool:
            visited.add(task_type)
            rec_stack.add(task_type)
            
            task = task_map.get(task_type)
            if task:
                for dep in task.depends_on:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(task_type)
            return False
        
        for task in tasks:
            if task.task_type not in visited:
                if dfs(task.task_type):
                    raise ValueError(f"Circular dependency detected in workflow")
    
    def get_execution_order(self, workflow: Workflow) -> List[Task]:
        """
        Get topological execution order of tasks.
        """
        task_map = {t.task_type: t for t in workflow.tasks}
        visited = set()
        order = []
        
        def dfs(task_type: TaskType):
            if task_type in visited:
                return
            visited.add(task_type)
            
            task = task_map.get(task_type)
            if task:
                for dep in task.depends_on:
                    if dep in task_map:
                        dfs(dep)
                order.append(task)
        
        for task in workflow.tasks:
            if task.task_type not in visited:
                dfs(task.task_type)
        
        return order
    
    def get_available_objectives(self) -> List[Dict[str, Any]]:
        """Get all available business objectives."""
        return list_objectives()