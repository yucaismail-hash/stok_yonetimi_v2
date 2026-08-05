# app/application/services/objective/business_objective_service.py
"""
Business Objective Service - DOCUMENT 07 REVISION 02
Domain-based application service for business objectives.

Application Services SHALL:
- Validate business requests
- Coordinate command handlers
- Coordinate workflows
- Coordinate transactions
- Generate responses

Application Services SHALL NEVER:
- Execute analytical logic
- Create AI Artifacts
- Perform learning
- Perform persistence directly
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging

from app.application.commands.base import RunBusinessObjectiveCommand
from app.application.handlers.run_business_objective_handler import RunBusinessObjectiveHandler
from app.application.response.schemas import APIResponse

logger = logging.getLogger(__name__)


class BusinessObjectiveService:
    """
    Business Objective Service - Domain-based application service.
    
    Responsible for business objective orchestration.
    """
    
    def __init__(self):
        self.handler = RunBusinessObjectiveHandler()
    
    async def run_objective(
        self,
        company_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        objective_type: str,
        params: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Run a business objective.
        
        Args:
            company_id: Company ID
            user_id: User ID
            dataset_id: Dataset ID
            objective_type: forecast, safety_stock, simulation, supplier, backtest
            params: Additional parameters
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with execution_id
        """
        logger.info(
            f"📊 BusinessObjectiveService.run_objective: {objective_type}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "dataset_id": str(dataset_id),
                "objective_type": objective_type,
            }
        )
        
        # Validate business request
        self._validate_objective_type(objective_type)
        
        # Create command
        command = RunBusinessObjectiveCommand(
            user_id=user_id,
            company_id=company_id,
            objective_type=objective_type,
            dataset_id=dataset_id,
            params=params,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        
        # Execute through handler
        return await self.handler.handle(command)
    
    def _validate_objective_type(self, objective_type: str) -> None:
        """Validate objective type."""
        valid_types = [
            "forecast",
            "safety_stock",
            "simulation",
            "supplier",
            "backtest",
            "seasonal_analysis",
            "trend_analysis",
        ]
        if objective_type not in valid_types:
            raise ValueError(f"Invalid objective type: {objective_type}. Must be one of: {valid_types}")