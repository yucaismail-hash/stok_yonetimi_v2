# app/application/services/execution/execution_service.py
"""
Execution Service - DOCUMENT 07 REVISION 02
Domain-based application service for execution operations.

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

from app.application.commands.base import RunSingleAnalysisCommand
from app.application.handlers.run_single_analysis_handler import RunSingleAnalysisHandler
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.application.response.schemas import APIResponse
from app.application.response.response_builder import ResponseBuilder

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Execution Service - Domain-based application service.
    
    Responsible for execution orchestration.
    """
    
    def __init__(self):
        self.handler = RunSingleAnalysisHandler()
        self.dispatcher = WorkflowDispatcher()
    
    async def run_analysis(
        self,
        company_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        analysis_type: str,
        material_codes: Optional[list[str]] = None,
        params: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Run a single analysis.
        
        Args:
            company_id: Company ID
            user_id: User ID
            dataset_id: Dataset ID
            analysis_type: forecast, safety_stock, simulation, supplier, backtest
            material_codes: Optional list of material codes
            params: Additional parameters
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with execution_id
        """
        logger.info(
            f"⚡ ExecutionService.run_analysis: {analysis_type}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "dataset_id": str(dataset_id),
                "analysis_type": analysis_type,
                "material_count": len(material_codes) if material_codes else 0,
            }
        )
        
        # Validate business request
        self._validate_analysis_type(analysis_type)
        
        # Create command
        command = RunSingleAnalysisCommand(
            user_id=user_id,
            company_id=company_id,
            analysis_type=analysis_type,
            dataset_id=dataset_id,
            material_codes=material_codes,
            params=params,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        
        # Execute through handler
        return await self.handler.handle(command)
    
    async def get_execution_status(
        self,
        execution_id: UUID,
        trace_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Get execution status.
        
        Args:
            execution_id: Execution ID
            trace_id: Trace ID for tracking
        
        Returns:
            APIResponse with execution status
        """
        logger.info(
            f"📊 ExecutionService.get_execution_status: {execution_id}",
            extra={
                "execution_id": str(execution_id),
            }
        )
        
        # Get status from dispatcher
        result = await self.dispatcher.get_execution_status(execution_id)
        
        return ResponseBuilder.success(
            data=result,
            message="Execution status retrieved successfully",
            execution_id=execution_id,
        )
    
    async def get_execution_result(
        self,
        execution_id: UUID,
        trace_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Get execution result.
        
        Args:
            execution_id: Execution ID
            trace_id: Trace ID for tracking
        
        Returns:
            APIResponse with execution result
        """
        logger.info(
            f"📊 ExecutionService.get_execution_result: {execution_id}",
            extra={
                "execution_id": str(execution_id),
            }
        )
        
        # Get result from dispatcher
        result = await self.dispatcher.get_execution_result(execution_id)
        
        return ResponseBuilder.success(
            data=result,
            message="Execution result retrieved successfully",
            execution_id=execution_id,
        )
    
    def _validate_analysis_type(self, analysis_type: str) -> None:
        """Validate analysis type."""
        valid_types = [
            "forecast",
            "safety_stock",
            "simulation",
            "supplier",
            "backtest",
            "seasonal_analysis",
            "trend_analysis",
        ]
        if analysis_type not in valid_types:
            raise ValueError(f"Invalid analysis type: {analysis_type}. Must be one of: {valid_types}")