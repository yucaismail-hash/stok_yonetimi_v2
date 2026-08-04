# app/engine/rule_engine.py
"""
Rule Engine - DOCUMENT 04 - PART 03
"""

from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
import logging

from app.engine.enums import TaskType, TaskStatus
from app.engine.workflow_engine import Workflow, Task
from app.engine.workflow_generator import WorkflowGenerator


logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """DOCUMENT 04 - Section 4: Rule Types"""
    DATASET = "dataset"
    BUSINESS = "business"
    LICENSE = "license"
    RESOURCE = "resource"
    CACHE = "cache"
    EXECUTION = "execution"


@dataclass
class RuleResult:
    """Result of a rule evaluation."""
    applied: bool
    modified_tasks: List[Task]
    skipped_tasks: List[Task]
    added_tasks: List[Task]
    reason: str
    rule_type: RuleType


@dataclass
class ExecutionPlan:
    """Execution plan with rules applied."""
    workflow: Workflow
    rules_applied: List[RuleResult]
    cache_hits: List[Dict[str, Any]]
    license_checks: List[Dict[str, Any]]
    resource_checks: List[Dict[str, Any]]


class RuleEngine:
    """
    Rule Engine - DOCUMENT 04 - Section 3
    
    Evaluates runtime conditions before execution.
    Modifies execution plans without changing Workflow Templates.
    """
    
    def __init__(self):
        self._rules = []
        self._license_cache = {}
    
    def evaluate_all(
        self,
        workflow: Workflow,
        dataset_info: Optional[Dict[str, Any]] = None,
        license_info: Optional[Dict[str, bool]] = None,
        resource_info: Optional[Dict[str, Any]] = None,
        cache_info: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """
        Evaluate all rules and create execution plan.
        """
        results = []
        cache_hits = []
        license_checks = []
        resource_checks = []
        
        # 1. Dataset Rules
        if dataset_info:
            dataset_result = self._evaluate_dataset_rules(workflow, dataset_info)
            if dataset_result:
                results.append(dataset_result)
        
        # 2. License Rules
        if license_info:
            license_result = self._evaluate_license_rules(workflow, license_info)
            if license_result:
                results.append(license_result)
                license_checks = self._get_license_checks(license_info)
        
        # 3. Cache Rules
        if cache_info:
            cache_result = self._evaluate_cache_rules(workflow, cache_info)
            if cache_result:
                results.append(cache_result)
                cache_hits = self._get_cache_hits(cache_info)
        
        # 4. Resource Rules
        if resource_info:
            resource_result = self._evaluate_resource_rules(workflow, resource_info)
            if resource_result:
                results.append(resource_result)
                resource_checks = self._get_resource_checks(resource_info)
        
        # 5. Business Rules
        business_result = self._evaluate_business_rules(workflow)
        if business_result:
            results.append(business_result)
        
        # 6. Execution Rules
        execution_result = self._evaluate_execution_rules(workflow)
        if execution_result:
            results.append(execution_result)
        
        return ExecutionPlan(
            workflow=workflow,
            rules_applied=results,
            cache_hits=cache_hits,
            license_checks=license_checks,
            resource_checks=resource_checks,
        )
    
    def _evaluate_dataset_rules(
        self,
        workflow: Workflow,
        dataset_info: Dict[str, Any],
    ) -> Optional[RuleResult]:
        """
        DOCUMENT 05 - Section 5: Dataset Rules
        """
        modified_tasks = []
        skipped_tasks = []
        added_tasks = []
        
        # Check dataset validity
        if not dataset_info.get("is_validated", True):
            # Stop workflow if dataset validation failed
            for task in workflow.tasks:
                task.status = TaskStatus.CANCELLED
                skipped_tasks.append(task)
            
            return RuleResult(
                applied=True,
                modified_tasks=modified_tasks,
                skipped_tasks=skipped_tasks,
                added_tasks=added_tasks,
                reason="Dataset validation failed - workflow stopped",
                rule_type=RuleType.DATASET,
            )
        
        # Check supplier dataset presence
        has_supplier = dataset_info.get("has_supplier_data", False)
        if not has_supplier:
            for task in workflow.tasks:
                if task.task_type == TaskType.SUPPLIER:
                    task.status = TaskStatus.SKIPPED
                    skipped_tasks.append(task)
            
            return RuleResult(
                applied=True,
                modified_tasks=modified_tasks,
                skipped_tasks=skipped_tasks,
                added_tasks=added_tasks,
                reason="Supplier dataset missing - skipping supplier analysis",
                rule_type=RuleType.DATASET,
            )
        
        # Check dataset length
        min_weeks = dataset_info.get("min_weeks_required", 8)
        actual_weeks = dataset_info.get("actual_weeks", 0)
        
        if actual_weeks < min_weeks:
            # Reduce backtest window
            for task in workflow.tasks:
                if task.task_type == TaskType.BACKTEST:
                    task.params["test_window"] = max(4, actual_weeks // 2)
                    modified_tasks.append(task)
            
            if modified_tasks:
                return RuleResult(
                    applied=True,
                    modified_tasks=modified_tasks,
                    skipped_tasks=skipped_tasks,
                    added_tasks=added_tasks,
                    reason=f"Dataset shorter than required ({actual_weeks} < {min_weeks}) - reduced backtest window",
                    rule_type=RuleType.DATASET,
                )
        
        return None
    
    def _evaluate_license_rules(
        self,
        workflow: Workflow,
        license_info: Dict[str, bool],
    ) -> Optional[RuleResult]:
        """
        DOCUMENT 04 - Section 6: License Rules
        """
        modified_tasks = []
        skipped_tasks = []
        added_tasks = []
        
        for task in workflow.tasks:
            task_key = task.task_type.value
            if task_key in license_info:
                if not license_info[task_key]:
                    # Task not licensed - skip it
                    if task.is_functional:
                        # Functional task - stop workflow
                        task.status = TaskStatus.CANCELLED
                        skipped_tasks.append(task)
                        return RuleResult(
                            applied=True,
                            modified_tasks=modified_tasks,
                            skipped_tasks=skipped_tasks,
                            added_tasks=added_tasks,
                            reason=f"Functional task {task_key} not licensed - workflow stopped",
                            rule_type=RuleType.LICENSE,
                        )
                    else:
                        # Enrichment task - skip it
                        task.status = TaskStatus.SKIPPED
                        skipped_tasks.append(task)
        
        if skipped_tasks:
            return RuleResult(
                applied=True,
                modified_tasks=modified_tasks,
                skipped_tasks=skipped_tasks,
                added_tasks=added_tasks,
                reason=f"Skipped unlicensed tasks: {[t.task_type.value for t in skipped_tasks]}",
                rule_type=RuleType.LICENSE,
            )
        
        return None
    
    def _evaluate_cache_rules(
        self,
        workflow: Workflow,
        cache_info: Dict[str, Any],
    ) -> Optional[RuleResult]:
        """
        DOCUMENT 04 - Section 7: Cache Rules
        """
        modified_tasks = []
        skipped_tasks = []
        added_tasks = []
        
        # Check if cache can be reused
        can_reuse = (
            cache_info.get("same_dataset_version", False) and
            cache_info.get("same_algorithm_version", False) and
            cache_info.get("same_configuration", False)
        )
        
        if can_reuse:
            # Mark tasks for cache reuse
            for task in workflow.tasks:
                task.params["use_cache"] = True
                task.params["cache_key"] = cache_info.get("cache_key")
                modified_tasks.append(task)
            
            return RuleResult(
                applied=True,
                modified_tasks=modified_tasks,
                skipped_tasks=skipped_tasks,
                added_tasks=added_tasks,
                reason="Cache eligible - reusing execution cache",
                rule_type=RuleType.CACHE,
            )
        
        return None
    
    def _evaluate_resource_rules(
        self,
        workflow: Workflow,
        resource_info: Dict[str, Any],
    ) -> Optional[RuleResult]:
        """
        DOCUMENT 04 - Section 8: Resource Rules
        """
        modified_tasks = []
        skipped_tasks = []
        added_tasks = []
        
        # Check resource availability
        worker_available = resource_info.get("worker_available", True)
        cpu_available = resource_info.get("cpu_available", True)
        memory_available = resource_info.get("memory_available", True)
        
        if not all([worker_available, cpu_available, memory_available]):
            # Delay execution
            for task in workflow.tasks:
                task.params["delayed"] = True
                task.params["delay_reason"] = "Resource constraints"
                modified_tasks.append(task)
            
            return RuleResult(
                applied=True,
                modified_tasks=modified_tasks,
                skipped_tasks=skipped_tasks,
                added_tasks=added_tasks,
                reason="Resource constraints detected - execution delayed",
                rule_type=RuleType.RESOURCE,
            )
        
        return None
    
    def _evaluate_business_rules(
        self,
        workflow: Workflow,
    ) -> Optional[RuleResult]:
        """
        DOCUMENT 04 - Section 4: Business Rules
        """
        modified_tasks = []
        skipped_tasks = []
        added_tasks = []
        
        # Check if dataset validation is required
        has_validation = any(
            t.task_type == TaskType.DATASET_VALIDATION
            for t in workflow.tasks
        )
        
        if not has_validation:
            # Add dataset validation if needed
            logger.warning("No dataset validation task found")
        
        return None
    
    def _evaluate_execution_rules(
        self,
        workflow: Workflow,
    ) -> Optional[RuleResult]:
        """
        DOCUMENT 04 - Section 4: Execution Rules
        """
        # Check for task dependencies
        for task in workflow.tasks:
            # Ensure tasks with dependencies are not in wrong order
            for dep in task.depends_on:
                dep_task = next(
                    (t for t in workflow.tasks if t.task_type == dep),
                    None
                )
                if dep_task and dep_task.order > task.order:
                    # Fix order
                    task.order, dep_task.order = dep_task.order, task.order
        
        return None
    
    def _get_license_checks(self, license_info: Dict[str, bool]) -> List[Dict[str, Any]]:
        """Get license check results."""
        return [
            {"feature": key, "licensed": value}
            for key, value in license_info.items()
        ]
    
    def _get_cache_hits(self, cache_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get cache hit information."""
        if cache_info.get("cache_hit"):
            return [{
                "cache_key": cache_info.get("cache_key"),
                "dataset_version": cache_info.get("dataset_version"),
                "algorithm_version": cache_info.get("algorithm_version"),
            }]
        return []
    
    def _get_resource_checks(self, resource_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get resource check results."""
        return [
            {
                "resource": key,
                "available": value,
                "utilization": resource_info.get(f"{key}_utilization", 0),
            }
            for key, value in resource_info.items()
            if key in ["worker", "cpu", "memory"]
        ]