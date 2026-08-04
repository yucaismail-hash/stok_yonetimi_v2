# app/engine/orchestrator.py
"""
Execution Orchestrator - DOCUMENT 04 - PART 03
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

from app.engine.enums import ExecutionState, TaskStatus
from app.engine.workflow_engine import WorkflowEngine, Workflow
from app.engine.rule_engine import RuleEngine
from app.engine.task_scheduler import TaskScheduler
from app.engine.worker_manager import WorkerManager
from app.engine.result_collector import ResultCollector


logger = logging.getLogger(__name__)


class ExecutionOrchestrator:
    """
    Execution Orchestrator - DOCUMENT 04 - PART 03
    
    Orchestrates the entire execution process.
    """
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.rule_engine = RuleEngine()
        self.task_scheduler = TaskScheduler()
        self.worker_manager = WorkerManager()
        self.result_collector = ResultCollector()
    
    def orchestrate(
        self,
        objective_type: str,
        dataset_id: str,
        user_id: str,
        company_id: str,
        params: Optional[Dict[str, Any]] = None,
        dataset_info: Optional[Dict[str, Any]] = None,
        license_info: Optional[Dict[str, bool]] = None,
        resource_info: Optional[Dict[str, Any]] = None,
        cache_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrate workflow execution.
        """
        # 1. Generate workflow
        workflow = self.workflow_engine.generate_workflow(
            objective_type=objective_type,
            dataset_id=dataset_id,
            user_id=user_id,
            company_id=company_id,
            params=params,
        )
        
        # 2. Evaluate rules
        execution_plan = self.rule_engine.evaluate_all(
            workflow=workflow,
            dataset_info=dataset_info,
            license_info=license_info,
            resource_info=resource_info,
            cache_info=cache_info,
        )
        
        # 3. Schedule tasks
        schedule = self.task_scheduler.schedule(
            workflow=workflow,
            available_workers=[w.worker_id for w in self.worker_manager.get_available_workers()],
        )
        
        # 4. Execute tasks
        results = self._execute_tasks(schedule, workflow)
        
        # 5. Collect results
        final_result = self.result_collector.collect(
            workflow=workflow,
            task_results=results,
        )
        
        return {
            "workflow_id": workflow.workflow_id,
            "status": workflow.state.value,
            "execution_plan": {
                "rules_applied": len(execution_plan.rules_applied),
                "cache_hits": execution_plan.cache_hits,
                "license_checks": execution_plan.license_checks,
            },
            "schedule": {
                "task_count": len(schedule.tasks),
                "parallel_groups": schedule.parallel_groups,
                "estimated_duration": schedule.total_estimated_duration,
            },
            "results": final_result,
        }
    
    def _execute_tasks(self, schedule, workflow: Workflow) -> List[Dict[str, Any]]:
        """Execute scheduled tasks."""
        results = []
        workflow.state = ExecutionState.RUNNING
        
        for task_group in schedule.parallel_groups:
            # Get tasks in this group
            group_tasks = [
                t for t in schedule.tasks
                if t.task.task_id in task_group
            ]
            
            # Execute in parallel if group has multiple tasks
            if len(group_tasks) > 1:
                # Parallel execution
                for scheduled_task in group_tasks:
                    result = self._execute_single_task(scheduled_task, workflow)
                    results.append(result)
            else:
                # Sequential execution
                for scheduled_task in group_tasks:
                    result = self._execute_single_task(scheduled_task, workflow)
                    results.append(result)
        
        # Check if all tasks completed
        all_completed = all(
            t.task.status == TaskStatus.COMPLETED
            for t in schedule.tasks
        )
        
        if all_completed:
            workflow.state = ExecutionState.COMPLETED
        else:
            workflow.state = ExecutionState.COMPLETED  # Partial completion
        
        workflow.completed_at = datetime.now()
        
        return results
    
    def _execute_single_task(self, scheduled_task, workflow: Workflow) -> Dict[str, Any]:
        """Execute a single task."""
        task = scheduled_task.task
        
        try:
            # Simulate task execution (analytical engines will be integrated later)
            task.started_at = datetime.now()
            task.status = TaskStatus.RUNNING
            
            # Execute task (placeholder)
            task.result = {
                "status": "completed",
                "message": f"Task {task.task_type.value} executed successfully",
                "output": {"sample": "data"},
            }
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            logger.info(f"✅ Task {task.task_type.value} completed")
            
            return {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "status": "completed",
                "result": task.result,
            }
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"❌ Task {task.task_type.value} failed: {str(e)}")
            
            return {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "status": "failed",
                "error": str(e),
            }