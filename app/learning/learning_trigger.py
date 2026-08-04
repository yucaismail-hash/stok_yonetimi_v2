# app/learning/learning_trigger.py
"""
Learning Trigger - DOCUMENT 05 - PART 01
Determines when learning should be triggered.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository


logger = logging.getLogger(__name__)


class LearningTrigger:
    """
    Learning Trigger - DOCUMENT 05
    
    Determines if learning should be triggered based on:
    - Execution Completed
    - Simulation Completed
    - Backtest Completed
    - Validated User Feedback
    - Dataset Revision
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
    
    def should_trigger(self, context: LearningContext) -> bool:
        """
        Determine if learning should be triggered.
        
        Returns:
            True if learning should start, False otherwise
        """
        # 1. Check if this is a valid learning trigger
        if not self._is_valid_trigger(context):
            logger.debug("Not a valid learning trigger")
            return False
        
        # 2. Check if execution was successful
        if not self._is_execution_successful(context):
            logger.debug("Execution was not successful")
            return False
        
        # 3. Check if minimum data requirements are met
        if not self._has_minimum_data(context):
            logger.debug("Minimum data requirements not met")
            return False
        
        return True
    
    def _is_valid_trigger(self, context: LearningContext) -> bool:
        """Check if this is a valid learning trigger."""
        # Check for valid execution
        if context.execution_id:
            return True
        
        # Check for valid user feedback
        if context.user_feedback:
            return True
        
        # Check for valid dataset revision
        if context.dataset_version > 1:
            return True
        
        return False
    
    def _is_execution_successful(self, context: LearningContext) -> bool:
        """Check if execution was successful."""
        # Check execution metrics
        metrics = context.execution_metrics
        if metrics.get("status") in ["completed", "success"]:
            return True
        
        # Check simulation results
        if context.simulation_results.get("status") == "completed":
            return True
        
        # Check backtest results
        if context.backtest_results.get("status") == "completed":
            return True
        
        return False
    
    def _has_minimum_data(self, context: LearningContext) -> bool:
        """Check if minimum data requirements are met."""
        # At least one result source should be present
        has_data = (
            context.simulation_results or
            context.backtest_results or
            context.user_feedback or
            context.external_intelligence
        )
        
        return bool(has_data)