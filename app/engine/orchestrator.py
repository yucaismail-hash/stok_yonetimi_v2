# app/engine/orchestrator.py
"""
Execution Orchestrator - DOCUMENT 04 - PART 03
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timezone
import logging

from app.engine.contracts import RuntimeAcceptance
from app.engine.enums import ExecutionState, TaskStatus
from app.engine.execution_context import ExecutionContext, ExecutionContextManager
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
        self.context_manager = ExecutionContextManager()

    async def accept(
        self,
        context: ExecutionContext,
        workflow: Workflow,
    ) -> RuntimeAcceptance:
        """Register an execution for runtime ownership without executing tasks."""
        if not isinstance(context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow must be a Workflow")
        if context.workflow is not workflow or context.workflow_id != workflow.workflow_id:
            raise ValueError("context and workflow identities must match")
        if context.state is not ExecutionState.CREATED:
            raise ValueError("only created contexts can be accepted")
        if context.queued_at is not None:
            raise ValueError("created context must not already have queued_at")

        # Phase 2D: standalone Forecast has PostgreSQL RuntimeStore authority.
        if context.analysis_type in ("forecast", "safety_stock", "simulation", "backtest", "supplier"):
            from app.database import SessionLocal
            from app.engine.runtime_store import RuntimeStore
            from app.models.runtime import RuntimeExecution
            session = SessionLocal()
            try:
                execution = RuntimeExecution(
                    execution_id=context.execution_id, company_id=context.company_id,
                    user_id=context.user_id, dataset_id=context.dataset_id,
                    workflow_id=context.workflow_id, analysis_type=context.analysis_type, state="queued",
                    current_stage="planning", progress=0, accepted_at=datetime.now(timezone.utc),
                    queued_at=datetime.now(timezone.utc), request_id=context.request_id,
                    trace_id=context.trace_id, correlation_id=context.correlation_id,
                    contract_version=context.contract_version,
                    metadata_={"params": context.params, "material_codes": context.material_codes},
                )
                task = workflow.tasks[0] if len(workflow.tasks) == 1 else None
                if task is None or workflow.capability.value not in ("demand_forecast", "safety_stock", "simulation", "backtest", "supplier_analysis"):
                    raise RuntimeError("standalone capability planning invariant failed")
                RuntimeStore(session).create_execution(execution, [{
                    "workflow_id": context.workflow_id, "task_id": task.task_id,
                    "capability": workflow.capability.value, "task_order": 0, "required": True,
                    "skippable": False, "dependencies": [], "state": "pending",
                    "max_attempts": task.retry_count, "timeout_seconds": task.timeout_seconds,
                }])
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
            accepted_at = datetime.now(timezone.utc)
            context.state = ExecutionState.QUEUED; context.queued_at = accepted_at
            return RuntimeAcceptance(context.execution_id, context.workflow_id, True, ExecutionState.QUEUED, accepted_at, f"Runtime accepted; {context.analysis_type} is queued durably.")

        accepted_at = datetime.now(timezone.utc)
        acceptance = RuntimeAcceptance(
            execution_id=context.execution_id,
            workflow_id=context.workflow_id,
            accepted=True,
            state=ExecutionState.QUEUED,
            accepted_at=accepted_at,
            message="Runtime accepted; execution has not started.",
        )
        self.context_manager.register_context(context)
        context.state = ExecutionState.QUEUED
        context.queued_at = accepted_at
        return acceptance
    
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
