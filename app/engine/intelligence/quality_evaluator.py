# app/engine/intelligence/quality_evaluator.py
"""
Quality Evaluator - DOCUMENT 04 - PART 05
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.engine.intelligence.models import ExecutionQuality
from app.engine.workflow_engine import Workflow


logger = logging.getLogger(__name__)


class QualityEvaluator:
    """
    Quality Evaluator - DOCUMENT 04 Section 12
    
    Evaluates execution quality.
    """
    
    def evaluate(
        self,
        workflow: Workflow,
        results: Dict[str, Any],
        metrics: Dict[str, Any],
    ) -> ExecutionQuality:
        """
        Evaluate execution quality.
        """
        correctness_score = self._evaluate_correctness(workflow, results)
        completeness_score = self._evaluate_completeness(workflow, results)
        reproducibility_score = self._evaluate_reproducibility(workflow)
        stability_score = self._evaluate_stability(metrics)
        efficiency_score = self._evaluate_efficiency(metrics)
        
        overall = (
            correctness_score * 0.30 +
            completeness_score * 0.20 +
            reproducibility_score * 0.20 +
            stability_score * 0.15 +
            efficiency_score * 0.15
        )
        
        return ExecutionQuality(
            workflow_id=workflow.workflow_id,
            correctness_score=correctness_score,
            completeness_score=completeness_score,
            reproducibility_score=reproducibility_score,
            stability_score=stability_score,
            efficiency_score=efficiency_score,
            overall_score=round(overall, 2),
            evaluated_at=datetime.now(),
        )
    
    def _evaluate_correctness(self, workflow: Workflow, results: Dict[str, Any]) -> float:
        """Evaluate execution correctness."""
        # Check if all functional tasks completed successfully
        functional_tasks = [t for t in workflow.tasks if t.is_functional]
        completed = [
            t for t in functional_tasks
            if t.status.value == "completed"
        ]
        
        if not functional_tasks:
            return 0.5
        
        return len(completed) / len(functional_tasks)
    
    def _evaluate_completeness(self, workflow: Workflow, results: Dict[str, Any]) -> float:
        """Evaluate execution completeness."""
        # Check if all tasks completed or skipped appropriately
        total_tasks = len(workflow.tasks)
        if total_tasks == 0:
            return 0.5
        
        valid_statuses = ["completed", "skipped"]
        valid_tasks = [
            t for t in workflow.tasks
            if t.status.value in valid_statuses
        ]
        
        return len(valid_tasks) / total_tasks
    
    def _evaluate_reproducibility(self, workflow: Workflow) -> float:
        """Evaluate execution reproducibility."""
        # Check if workflow has version and can be reproduced
        return 0.9 if hasattr(workflow, 'version') else 0.5
    
    def _evaluate_stability(self, metrics: Dict[str, Any]) -> float:
        """Evaluate execution stability."""
        retry_count = metrics.get("retry_count", 0)
        if retry_count == 0:
            return 1.0
        elif retry_count <= 2:
            return 0.8
        elif retry_count <= 5:
            return 0.5
        else:
            return 0.3
    
    def _evaluate_efficiency(self, metrics: Dict[str, Any]) -> float:
        """Evaluate execution efficiency."""
        duration = metrics.get("duration_ms", 0)
        if duration == 0:
            return 0.5
        
        # Compare to expected duration
        expected = metrics.get("expected_duration_ms", duration)
        
        if duration <= expected:
            return 1.0
        elif duration <= expected * 1.5:
            return 0.7
        elif duration <= expected * 2:
            return 0.5
        else:
            return 0.3