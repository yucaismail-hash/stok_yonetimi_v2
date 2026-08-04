# app/engine/intelligence/decision_logger.py
"""
Decision Logger - DOCUMENT 04 - PART 05
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

from app.engine.intelligence.models import (
    DecisionLog,
    DecisionType,
    RuleDecisionLog,
    WorkflowExplanation,
    TaskExplanation,
)


logger = logging.getLogger(__name__)


class DecisionLogger:
    """
    Decision Logger - DOCUMENT 04 Section 3 & 4
    
    Records all execution decisions.
    """
    
    def __init__(self):
        self._decision_logs: Dict[str, List[DecisionLog]] = {}
        self._rule_logs: Dict[str, List[RuleDecisionLog]] = {}
        self._workflow_explanations: Dict[str, WorkflowExplanation] = {}
        self._task_explanations: Dict[str, List[TaskExplanation]] = {}
    
    def log_decision(
        self,
        workflow_id: str,
        decision_type: DecisionType,
        business_objective: str,
        workflow_version: str,
        rule_decisions: List[Dict[str, Any]],
        execution_plan: Dict[str, Any],
        skipped_tasks: List[str],
        conditional_tasks: List[Dict[str, Any]],
        optimization_decisions: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionLog:
        """Log an execution decision."""
        decision_log = DecisionLog(
            decision_id=str(uuid4()),
            workflow_id=workflow_id,
            decision_type=decision_type,
            business_objective=business_objective,
            workflow_version=workflow_version,
            rule_decisions=rule_decisions,
            execution_plan=execution_plan,
            skipped_tasks=skipped_tasks,
            conditional_tasks=conditional_tasks,
            optimization_decisions=optimization_decisions,
            metadata=metadata or {},
        )
        
        if workflow_id not in self._decision_logs:
            self._decision_logs[workflow_id] = []
        self._decision_logs[workflow_id].append(decision_log)
        
        logger.info(f"📝 Decision logged: {decision_type.value} for {workflow_id}")
        
        return decision_log
    
    def log_rule_decision(
        self,
        rule_id: str,
        rule_type: str,
        reason: str,
        decision: str,
        task_id: Optional[str] = None,
        task_type: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuleDecisionLog:
        """Log a rule engine decision."""
        rule_log = RuleDecisionLog(
            rule_id=rule_id,
            rule_type=rule_type,
            reason=reason,
            decision=decision,
            task_id=task_id,
            task_type=task_type,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata or {},
        )
        
        if rule_type not in self._rule_logs:
            self._rule_logs[rule_type] = []
        self._rule_logs[rule_type].append(rule_log)
        
        logger.info(f"📝 Rule decision logged: {rule_id} - {decision}")
        
        return rule_log
    
    def log_workflow_explanation(
        self,
        workflow_id: str,
        generation_reason: str,
        skipped_tasks: List[Dict[str, str]],
        reordered_tasks: List[Dict[str, str]],
        parallel_execution_reason: str,
        cache_decision: Dict[str, Any],
        stop_reason: Optional[str] = None,
    ) -> WorkflowExplanation:
        """Log workflow explanation."""
        explanation = WorkflowExplanation(
            workflow_id=workflow_id,
            generation_reason=generation_reason,
            skipped_tasks=skipped_tasks,
            reordered_tasks=reordered_tasks,
            parallel_execution_reason=parallel_execution_reason,
            cache_decision=cache_decision,
            stop_reason=stop_reason,
        )
        
        self._workflow_explanations[workflow_id] = explanation
        
        logger.info(f"📝 Workflow explanation logged: {workflow_id}")
        
        return explanation
    
    def log_task_explanation(
        self,
        task_id: str,
        task_type: str,
        execution_reason: str,
        input_source: str,
        output_destination: str,
        dependency_status: str,
        execution_duration_ms: Optional[float] = None,
        worker_assignment: Optional[str] = None,
        execution_result: Optional[Dict[str, Any]] = None,
    ) -> TaskExplanation:
        """Log task explanation."""
        explanation = TaskExplanation(
            task_id=task_id,
            task_type=task_type,
            execution_reason=execution_reason,
            input_source=input_source,
            output_destination=output_destination,
            dependency_status=dependency_status,
            execution_duration_ms=execution_duration_ms,
            worker_assignment=worker_assignment,
            execution_result=execution_result or {},
        )
        
        if task_id not in self._task_explanations:
            self._task_explanations[task_id] = []
        self._task_explanations[task_id].append(explanation)
        
        logger.info(f"📝 Task explanation logged: {task_id}")
        
        return explanation
    
    def get_decision_logs(self, workflow_id: str) -> List[DecisionLog]:
        """Get all decision logs for a workflow."""
        return self._decision_logs.get(workflow_id, [])
    
    def get_rule_logs(self, rule_type: Optional[str] = None) -> List[RuleDecisionLog]:
        """Get rule logs."""
        if rule_type:
            return self._rule_logs.get(rule_type, [])
        all_logs = []
        for logs in self._rule_logs.values():
            all_logs.extend(logs)
        return all_logs
    
    def get_workflow_explanation(self, workflow_id: str) -> Optional[WorkflowExplanation]:
        """Get workflow explanation."""
        return self._workflow_explanations.get(workflow_id)
    
    def get_task_explanations(self, task_id: str) -> List[TaskExplanation]:
        """Get task explanations."""
        return self._task_explanations.get(task_id, [])