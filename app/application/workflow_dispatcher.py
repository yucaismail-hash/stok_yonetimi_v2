# app/application/workflow_dispatcher.py
"""
Workflow Dispatcher - DOCUMENT 07 APP-010
Single orchestration gateway for workflow execution.

Application Services SHALL NOT communicate directly with Workflow Engine.

Architecture:
Application Service
    ↓
Workflow Dispatcher
    ↓
Workflow Engine

WorkflowDispatcher SHALL become the single orchestration gateway.
Future integrations (Queue, CLI, Scheduler, Webhook, Batch Processing)
SHALL all reuse WorkflowDispatcher.
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging
from uuid_extensions import uuid7

from app.application.models.trace_context import TraceContextHolder
from app.engine.contracts import WorkflowDispatchRequest, WorkflowDispatchResult
from app.engine.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class WorkflowDispatcher:
    """
    Workflow Dispatcher - Single orchestration gateway.
    
    DOCUMENT 07 APP-010
    """
    
    def __init__(self, workflow_engine=None):
        self.workflow_engine = workflow_engine or WorkflowEngine()

    @staticmethod
    def _trace_values(trace_context) -> Dict[str, Optional[str]]:
        return {
            "trace_id": trace_context.trace_id if trace_context else None,
            "correlation_id": trace_context.correlation_id if trace_context else None,
            "request_id": trace_context.request_id if trace_context else None,
        }

    @staticmethod
    def _dispatch_response(
        result: WorkflowDispatchResult,
        message: str,
    ) -> Dict[str, Any]:
        return {
            "execution_id": result.execution_id,
            "status": result.state.value,
            "message": result.message or message,
            "trace_id": result.trace_id,
        }
    
    async def dispatch_business_objective(
        self,
        company_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        objective_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Dispatch a business objective workflow.
        
        Business Objective executions SHALL NOT specify analytical engines.
        Workflow Engine SHALL determine which engines are required.
        
        Args:
            company_id: Company ID
            user_id: User ID
            dataset_id: Dataset ID
            objective_type: forecast, safety_stock, simulation, supplier, backtest
            params: Additional parameters
        
        Returns:
            Execution result with execution_id
        """
        trace_context = TraceContextHolder.get_context()
        
        logger.info(
            f"🚀 Dispatching business objective: {objective_type}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "dataset_id": str(dataset_id),
                "objective_type": objective_type,
                "trace_id": trace_context.trace_id if trace_context else None,
            }
        )
        
        trace_values = self._trace_values(trace_context)
        request = WorkflowDispatchRequest(
            execution_id=uuid7(),
            company_id=company_id,
            user_id=user_id,
            dataset_id=dataset_id,
            objective_type=objective_type,
            params=params or {},
            **trace_values,
        )
        
        # Dispatch through workflow engine
        result = await self.workflow_engine.dispatch(request)
        
        # Update trace context with execution_id
        if trace_context:
            trace_context.execution_id = result.execution_id
        
        logger.info(
            f"✅ Business objective dispatched: {objective_type}",
            extra={
                "execution_id": str(result.execution_id),
                "trace_id": trace_context.trace_id if trace_context else None,
            }
        )
        
        return self._dispatch_response(
            result,
            f"Business objective '{objective_type}' started successfully",
        )
    
    async def dispatch_single_analysis(
        self,
        company_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        analysis_type: str,
        material_codes: Optional[list[str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Dispatch a single analysis workflow.
        
        Single Analysis requests SHALL also use Workflow Dispatcher.
        The execution flow SHALL remain identical.
        
        Args:
            company_id: Company ID
            user_id: User ID
            dataset_id: Dataset ID
            analysis_type: forecast, safety_stock, simulation, supplier, backtest
            material_codes: Optional list of material codes to analyze
            params: Additional parameters
        
        Returns:
            Execution result with execution_id
        """
        trace_context = TraceContextHolder.get_context()
        
        logger.info(
            f"🚀 Dispatching single analysis: {analysis_type}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "dataset_id": str(dataset_id),
                "analysis_type": analysis_type,
                "material_count": len(material_codes) if material_codes else 0,
                "trace_id": trace_context.trace_id if trace_context else None,
            }
        )
        
        trace_values = self._trace_values(trace_context)
        request = WorkflowDispatchRequest(
            execution_id=uuid7(),
            company_id=company_id,
            user_id=user_id,
            dataset_id=dataset_id,
            analysis_type=analysis_type,
            material_codes=material_codes,
            params=params or {},
            **trace_values,
        )
        
        # Dispatch through workflow engine
        result = await self.workflow_engine.dispatch(request)
        
        # Update trace context with execution_id
        if trace_context:
            trace_context.execution_id = result.execution_id
        
        logger.info(
            f"✅ Single analysis dispatched: {analysis_type}",
            extra={
                "execution_id": str(result.execution_id),
                "trace_id": trace_context.trace_id if trace_context else None,
            }
        )
        
        return self._dispatch_response(
            result,
            f"Analysis '{analysis_type}' started successfully",
        )
    
    async def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """
        Get execution status.
        """
        snapshot = await self.workflow_engine.get_execution_status(execution_id)
        return snapshot.to_dict()
    
    async def get_execution_result(self, execution_id: UUID) -> Dict[str, Any]:
        """
        Get execution result.
        """
        envelope = await self.workflow_engine.get_execution_result(execution_id)
        return envelope.to_dict()
