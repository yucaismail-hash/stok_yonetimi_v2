# app/engine/intelligence/predictor.py
"""
Execution Predictor - DOCUMENT 04 - PART 05
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.engine.intelligence.models import ExecutionPrediction
from app.engine.intelligence.execution_memory import ExecutionMemoryManager


logger = logging.getLogger(__name__)


class ExecutionPredictor:
    """
    Execution Predictor - DOCUMENT 04 Section 9
    
    Estimates expected execution characteristics.
    Improves using historical executions.
    """
    
    def __init__(self):
        self.memory_manager = ExecutionMemoryManager()
    
    def predict(
        self,
        workflow_id: str,
        task_count: int,
        sku_count: int,
        complexity_score: float = 1.0,
    ) -> ExecutionPrediction:
        """Predict execution characteristics."""
        # Get historical learning
        learning = self.memory_manager.get_learning(workflow_id)
        
        if learning and learning.sample_count > 0:
            # Use historical data for prediction
            base_duration = learning.avg_workflow_duration_ms or 60000
            sku_factor = 1 + (sku_count / 100)
            complexity_factor = complexity_score
            
            expected_duration = base_duration * sku_factor * complexity_factor
            
            confidence = min(0.95, 0.5 + (learning.sample_count / 50))
        else:
            # Fallback prediction
            expected_duration = task_count * 30000 + sku_count * 1000
            confidence = 0.3
        
        expected_workers = max(1, min(4, task_count // 2))
        expected_cost = expected_duration / 1000 * 0.001
        
        return ExecutionPrediction(
            workflow_id=workflow_id,
            expected_duration_ms=expected_duration,
            expected_resource_usage={
                "cpu_percent": 30 + (sku_count / 100) * 20,
                "memory_mb": 512 + (sku_count / 10) * 10,
            },
            expected_worker_count=expected_workers,
            expected_cost=expected_cost,
            expected_queue_time_ms=expected_duration * 0.1,
            confidence_score=confidence,
            generated_at=datetime.now(),
        )
    
    def improve_with_history(
        self,
        workflow_id: str,
        actual_duration_ms: float,
        actual_workers: int,
        actual_sku_count: int,
    ):
        """Improve predictions with historical data."""
        # Calculate actual metrics
        avg_sku_processing = actual_duration_ms / max(1, actual_sku_count)
        
        # Update learning
        self.memory_manager.update_learning(
            workflow_id=workflow_id,
            avg_duration_ms=actual_duration_ms,
            avg_sku_processing_ms=avg_sku_processing,
            worker_performance={f"worker_{i}": 1.0 for i in range(actual_workers)},
        )
        
        logger.info(f"📈 Predictor improved with history: {workflow_id}")