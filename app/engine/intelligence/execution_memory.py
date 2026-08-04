# app/engine/intelligence/execution_memory.py
"""
Execution Memory - DOCUMENT 04 - PART 05
"""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import logging

from app.engine.intelligence.models import (
    ExecutionMemory,
    ExecutionLearning,
    RuleDecisionLog,
)


logger = logging.getLogger(__name__)


class ExecutionMemoryManager:
    """
    Execution Memory - DOCUMENT 04 Section 7
    
    Stores execution behaviour. Never stores raw datasets.
    """
    
    def __init__(self):
        self._memories: Dict[str, ExecutionMemory] = {}
        self._learnings: Dict[str, ExecutionLearning] = {}
    
    def create_memory(
        self,
        workflow_pattern: Dict[str, Any],
        execution_characteristics: Dict[str, Any],
        rule_history: List[RuleDecisionLog],
        optimization_history: List[Dict[str, Any]],
        execution_statistics: Dict[str, Any],
    ) -> ExecutionMemory:
        """Create execution memory."""
        memory = ExecutionMemory(
            memory_id=str(uuid4()),
            workflow_pattern=workflow_pattern,
            execution_characteristics=execution_characteristics,
            rule_history=rule_history,
            optimization_history=optimization_history,
            execution_statistics=execution_statistics,
        )
        
        self._memories[memory.memory_id] = memory
        
        logger.info(f"🧠 Execution memory created: {memory.memory_id}")
        
        return memory
    
    def update_memory(
        self,
        memory_id: str,
        workflow_pattern: Optional[Dict[str, Any]] = None,
        execution_characteristics: Optional[Dict[str, Any]] = None,
        rule_history: Optional[List[RuleDecisionLog]] = None,
        optimization_history: Optional[List[Dict[str, Any]]] = None,
        execution_statistics: Optional[Dict[str, Any]] = None,
    ) -> Optional[ExecutionMemory]:
        """Update execution memory."""
        memory = self._memories.get(memory_id)
        if not memory:
            return None
        
        if workflow_pattern:
            memory.workflow_pattern = workflow_pattern
        if execution_characteristics:
            memory.execution_characteristics = execution_characteristics
        if rule_history:
            memory.rule_history = rule_history
        if optimization_history:
            memory.optimization_history = optimization_history
        if execution_statistics:
            memory.execution_statistics = execution_statistics
        
        memory.updated_at = datetime.now()
        
        return memory
    
    def get_memory(self, memory_id: str) -> Optional[ExecutionMemory]:
        """Get execution memory."""
        return self._memories.get(memory_id)
    
    def get_all_memories(self) -> List[ExecutionMemory]:
        """Get all execution memories."""
        return list(self._memories.values())
    
    def update_learning(
        self,
        workflow_id: str,
        avg_duration_ms: Optional[float] = None,
        avg_sku_processing_ms: Optional[float] = None,
        avg_workflow_duration_ms: Optional[float] = None,
        worker_performance: Optional[Dict[str, float]] = None,
        cache_efficiency: Optional[float] = None,
        failure_frequency: Optional[float] = None,
    ) -> ExecutionLearning:
        """Update execution learning."""
        learning = self._learnings.get(workflow_id)
        
        if not learning:
            learning = ExecutionLearning(
                workflow_id=workflow_id,
                sample_count=0,
            )
        
        if avg_duration_ms is not None:
            learning.avg_duration_ms = avg_duration_ms
        if avg_sku_processing_ms is not None:
            learning.avg_sku_processing_ms = avg_sku_processing_ms
        if avg_workflow_duration_ms is not None:
            learning.avg_workflow_duration_ms = avg_workflow_duration_ms
        if worker_performance is not None:
            learning.worker_performance = worker_performance
        if cache_efficiency is not None:
            learning.cache_efficiency = cache_efficiency
        if failure_frequency is not None:
            learning.failure_frequency = failure_frequency
        
        learning.sample_count += 1
        learning.last_updated = datetime.now()
        
        self._learnings[workflow_id] = learning
        
        logger.info(f"📊 Execution learning updated: {workflow_id}")
        
        return learning
    
    def get_learning(self, workflow_id: str) -> Optional[ExecutionLearning]:
        """Get execution learning."""
        return self._learnings.get(workflow_id)
    
    def get_all_learnings(self) -> List[ExecutionLearning]:
        """Get all execution learnings."""
        return list(self._learnings.values())