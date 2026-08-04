# app/engine/workflow_engine.py
"""
Workflow Engine - DOCUMENT 04 - PART 02
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime
import logging
from app.engine.capability_registry import capability_registry, Capability

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
from app.engine.workflow_generator import Workflow, Task, WorkflowGenerator


logger = logging.getLogger(__name__)


class DependencyType(str, Enum):
    """DOCUMENT 04 - Section 6: Dependency Types"""
    FUNCTIONAL = "functional"
    ENRICHMENT = "enrichment"


@dataclass
class DependencyResolution:
    """Result of dependency resolution."""
    resolved: bool
    functional_available: List[TaskType]
    functional_missing: List[TaskType]
    enrichment_available: List[TaskType]
    enrichment_skipped: List[TaskType]
    can_execute: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class WorkflowTemplate:
    """DOCUMENT 04 - Section 5: Workflow Template"""
    template_id: str
    objective_type: BusinessObjective
    name: str
    description: str
    steps: List[WorkflowStep]
    version: str = "1.0.0"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class WorkflowEngine:
    """
    Workflow Engine - DOCUMENT 04 - PART 02
    
    Transforms Business Objectives into executable workflows.
    Does NOT execute analytical tasks.
    """
    
    def __init__(self):
        self.generator = WorkflowGenerator()
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default workflow templates from registry."""
        for objective_type, objective_def in OBJECTIVE_REGISTRY.items():
            template = WorkflowTemplate(
                template_id=str(uuid4()),
                objective_type=objective_def.objective_type,
                name=objective_def.name,
                description=objective_def.description,
                steps=objective_def.steps,
                version="1.0.0",
                is_active=True,
            )
            self._templates[objective_type.value] = template
        logger.info(f"✅ Loaded {len(self._templates)} workflow templates")
    
    def get_template(self, objective_type: BusinessObjective) -> Optional[WorkflowTemplate]:
        """Get workflow template by objective type."""
        return self._templates.get(objective_type.value)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all workflow templates."""
        return [
            {
                "template_id": t.template_id,
                "objective_type": t.objective_type.value,
                "name": t.name,
                "description": t.description,
                "version": t.version,
                "is_active": t.is_active,
                "step_count": len(t.steps),
                "created_at": t.created_at.isoformat(),
            }
            for t in self._templates.values()
        ]
    
    def generate_workflow(
        self,
        objective_type: BusinessObjective,
        dataset_id: str,
        user_id: str,
        company_id: str,
        params: Optional[Dict[str, Any]] = None,
        available_engines: Optional[Set[str]] = None,
    ) -> Workflow:
        """
        Generate an executable workflow from a business objective.
        
        DOCUMENT 04 - Section 4: Workflow Generation
        """
        # 1. Get template
        template = self.get_template(objective_type)
        if not template:
            raise ValueError(f"No workflow template for: {objective_type}")
        
        if not template.is_active:
            raise ValueError(f"Workflow template is inactive: {objective_type}")
        
        # 2. Generate base workflow
        workflow = self.generator.generate(
            objective_type=objective_type,
            dataset_id=dataset_id,
            user_id=user_id,
            company_id=company_id,
            params=params,
        )
        
        # 3. Check available engines
        if available_engines:
            workflow = self._filter_by_available_engines(workflow, available_engines)
        
        # 4. Resolve dependencies
        resolution = self.resolve_dependencies(workflow)
        
        if not resolution.can_execute:
            raise ValueError(
                f"Cannot execute workflow: Missing functional dependencies: "
                f"{resolution.functional_missing}"
            )
        
        # 5. Log skipped enrichments
        if resolution.enrichment_skipped:
            logger.info(
                f"Skipped enrichment tasks: {[t.value for t in resolution.enrichment_skipped]}"
            )
        
        # 6. Validate workflow
        self.validate_workflow(workflow)
        
        # 7. Set execution order
        workflow.state = ExecutionState.CREATED
        
        logger.info(f"✅ Workflow generated: {workflow.workflow_id}")
        
        return workflow
    
    def _filter_by_available_engines(
        self,
        workflow: Workflow,
        available_engines: Set[str],
    ) -> Workflow:
        """
        Filter tasks by available engines.
        DOCUMENT 04 - Section 2: Skip unavailable optional engines
        """
        filtered_tasks = []
        
        for task in workflow.tasks:
            task_name = task.task_type.value
            
            # Functional tasks must be available
            if task.is_functional:
                if task_name not in available_engines:
                    raise ValueError(
                        f"Functional task {task_name} not available in: {available_engines}"
                    )
                filtered_tasks.append(task)
            else:
                # Enrichment tasks - skip if not available
                if task_name in available_engines:
                    filtered_tasks.append(task)
                else:
                    task.status = TaskStatus.SKIPPED
                    logger.info(f"Skipping unavailable enrichment: {task_name}")
                    filtered_tasks.append(task)  # Still keep for graph integrity
        
        workflow.tasks = filtered_tasks
        return workflow
    
    def resolve_dependencies(self, workflow: Workflow) -> DependencyResolution:
        """
        Resolve task dependencies.
        DOCUMENT 04 - Section 6: Dependency Types
        """
        functional_available = []
        functional_missing = []
        enrichment_available = []
        enrichment_skipped = []
        errors = []
        
        task_map = {t.task_type: t for t in workflow.tasks}
        
        for task in workflow.tasks:
            if task.is_functional:
                # Check if all functional dependencies are available
                missing = []
                for dep in task.depends_on:
                    if dep not in task_map:
                        missing.append(dep)
                    elif task_map[dep].status == TaskStatus.SKIPPED:
                        missing.append(dep)
                
                if missing:
                    functional_missing.extend(missing)
                    errors.append(
                        f"Functional task {task.task_type.value} missing dependencies: "
                        f"{[t.value for t in missing]}"
                    )
                else:
                    functional_available.append(task.task_type)
            else:
                # Enrichment - can be skipped
                if task.status == TaskStatus.SKIPPED:
                    enrichment_skipped.append(task.task_type)
                else:
                    enrichment_available.append(task.task_type)
        
        can_execute = len(functional_missing) == 0
        
        return DependencyResolution(
            resolved=can_execute,
            functional_available=functional_available,
            functional_missing=functional_missing,
            enrichment_available=enrichment_available,
            enrichment_skipped=enrichment_skipped,
            can_execute=can_execute,
            errors=errors,
        )
    
    def validate_workflow(self, workflow: Workflow) -> bool:
        """
        Validate workflow integrity.
        DOCUMENT 04 - Section 12: Workflow Validation
        """
        # 1. Check duplicate tasks
        task_types = [t.task_type for t in workflow.tasks]
        if len(task_types) != len(set(task_types)):
            duplicates = [t for t in task_types if task_types.count(t) > 1]
            raise ValueError(f"Duplicate tasks found: {[t.value for t in set(duplicates)]}")
        
        # 2. Check circular dependencies
        self._check_circular_dependencies(workflow.tasks)
        
        # 3. Check missing tasks
        task_map = {t.task_type: t for t in workflow.tasks}
        for task in workflow.tasks:
            for dep in task.depends_on:
                if dep not in task_map:
                    raise ValueError(
                        f"Task {task.task_type.value} depends on {dep.value} "
                        f"which is missing"
                    )
        
        # 4. Check business rules
        self._validate_business_rules(workflow)
        
        logger.info(f"✅ Workflow validated: {workflow.workflow_id}")
        
        return True
    
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
                    raise ValueError("Circular dependency detected in workflow")
    
    def _validate_business_rules(self, workflow: Workflow):
        """Validate business rules for workflow."""
        # Dataset validation must be completed
        dataset_validated = False
        for task in workflow.tasks:
            if task.task_type == TaskType.DATASET_VALIDATION:
                dataset_validated = True
                break
        
        # If dataset validation is required, check if it's included
        if any(t.is_functional for t in workflow.tasks):
            # At least one task requires dataset validation
            if not dataset_validated:
                logger.warning(
                    "No dataset validation task found. "
                    "Consider adding DATASET_VALIDATION to workflow."
                )
    
    def get_execution_graph(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Get execution graph (DAG) representation.
        DOCUMENT 04 - Section 7: Execution Graph
        """
        nodes = []
        edges = []
        
        for task in workflow.tasks:
            nodes.append({
                "id": task.task_id,
                "type": task.task_type.value,
                "functional": task.is_functional,
                "status": task.status.value,
                "priority": task.priority.value,
            })
            
            for dep in task.depends_on:
                # Find dependency task
                for t in workflow.tasks:
                    if t.task_type == dep:
                        edges.append({
                            "from": t.task_id,
                            "to": task.task_id,
                            "type": "functional" if task.is_functional else "enrichment",
                        })
                        break
        
        return {
            "workflow_id": workflow.workflow_id,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "is_dag": self._is_dag(workflow),
        }
    
    def _is_dag(self, workflow: Workflow) -> bool:
        """Check if workflow graph is a DAG."""
        try:
            self._check_circular_dependencies(workflow.tasks)
            return True
        except ValueError:
            return False
    
    def get_execution_plan(self, workflow: Workflow) -> List[Dict[str, Any]]:
        """
        Get execution plan with ordered tasks.
        DOCUMENT 04 - Section 4: Task Plan
        """
        order = self.generator.get_execution_order(workflow)
        
        plan = []
        for task in order:
            plan.append({
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "order": task.order,
                "priority": task.priority.value,
                "depends_on": [t.value for t in task.depends_on],
                "is_functional": task.is_functional,
                "estimated_timeout": task.timeout_seconds,
                "retry_count": task.retry_count,
            })
        
        return plan
    
    def register_template(self, template: WorkflowTemplate):
        """Register a new workflow template."""
        self._templates[template.objective_type.value] = template
        logger.info(f"✅ Template registered: {template.objective_type.value}")
    
    def update_template(
        self,
        objective_type: BusinessObjective,
        steps: List[WorkflowStep],
        version: str,
    ) -> Optional[WorkflowTemplate]:
        """Update an existing workflow template."""
        template = self.get_template(objective_type)
        if not template:
            return None
        
        template.steps = steps
        template.version = version
        template.updated_at = datetime.now()
        
        logger.info(f"✅ Template updated: {objective_type.value} v{version}")
        
        return template
    def _get_engine_for_task(self, task_type: str) -> Optional[Any]:
        """Get engine for a task type through Capability Registry."""
        # Map task type to capability
        capability_map = {
            "forecast": Capability.DEMAND_FORECAST,
            "safety_stock": Capability.SAFETY_STOCK,
            "simulation": Capability.SIMULATION,
            "backtest": Capability.BACKTEST,
            "supplier": Capability.SUPPLIER_ANALYSIS,
            "pattern": Capability.PATTERN_ANALYSIS,
        }
        
        capability = capability_map.get(task_type)
        if not capability:
            return None
        
        return capability_registry.get_engine(capability)