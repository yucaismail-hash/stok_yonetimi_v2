# app/engine/result_collector.py
"""
Result Collector - DOCUMENT 04 - PART 03
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.engine.enums import TaskStatus, ExecutionState
from app.engine.workflow_engine import Workflow


logger = logging.getLogger(__name__)


class ResultCollector:
    """
    Result Collector - DOCUMENT 04 - Section 16
    
    Collects outputs, validates outputs, stores outputs,
    triggers notifications, triggers learning.
    """
    
    def collect(
        self,
        workflow: Workflow,
        task_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Collect results from task executions.
        """
        # 1. Collect outputs
        outputs = self._collect_outputs(workflow, task_results)
        
        # 2. Validate outputs
        validation = self._validate_outputs(workflow, outputs)
        
        # 3. Store outputs
        stored = self._store_outputs(workflow, outputs, validation)
        
        # 4. Trigger notifications
        notifications = self._trigger_notifications(workflow, validation)
        
        # 5. Trigger learning
        learning_trigger = self._trigger_learning(workflow, outputs)
        
        return {
            "workflow_id": workflow.workflow_id,
            "status": workflow.state.value,
            "outputs": outputs,
            "validation": validation,
            "stored": stored,
            "notifications": notifications,
            "learning_triggered": learning_trigger,
            "collected_at": datetime.now().isoformat(),
        }
    
    def _collect_outputs(
        self,
        workflow: Workflow,
        task_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Collect outputs from tasks."""
        outputs = {}
        
        for result in task_results:
            if result.get("status") == "completed":
                outputs[result["task_type"]] = result.get("result", {})
            else:
                outputs[result["task_type"]] = {
                    "error": result.get("error", "Unknown error"),
                }
        
        return outputs
    
    def _validate_outputs(
        self,
        workflow: Workflow,
        outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate outputs."""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
        }
        
        for task_type, output in outputs.items():
            if output.get("error"):
                validation["is_valid"] = False
                validation["errors"].append({
                    "task": task_type,
                    "error": output["error"],
                })
        
        return validation
    
    def _store_outputs(
        self,
        workflow: Workflow,
        outputs: Dict[str, Any],
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Store outputs."""
        # Placeholder - actual storage will be implemented later
        return {
            "stored": True,
            "storage_location": f"workflow_results/{workflow.workflow_id}",
            "output_count": len(outputs),
            "stored_at": datetime.now().isoformat(),
        }
    
    def _trigger_notifications(
        self,
        workflow: Workflow,
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Trigger notifications based on execution results."""
        notifications = []
        
        if workflow.state == ExecutionState.COMPLETED:
            notifications.append({
                "type": "success",
                "title": "Workflow Completed",
                "message": f"Workflow {workflow.workflow_id} completed successfully",
            })
        else:
            notifications.append({
                "type": "warning",
                "title": "Workflow Partial",
                "message": f"Workflow {workflow.workflow_id} completed with issues",
            })
        
        return {
            "triggered": len(notifications) > 0,
            "notifications": notifications,
        }
    
    def _trigger_learning(
        self,
        workflow: Workflow,
        outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Trigger learning after execution.
        DOCUMENT 04 - Section 15: Learning Trigger
        """
        if workflow.state == ExecutionState.COMPLETED:
            return {
                "triggered": True,
                "phases": [
                    "Company Learning",
                    "Pattern Intelligence",
                    "Decision Learning",
                ],
                "message": "Learning triggered after successful execution",
            }
        else:
            return {
                "triggered": False,
                "reason": "Execution not completed successfully",
            }