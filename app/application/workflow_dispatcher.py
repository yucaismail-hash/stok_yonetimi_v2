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

from app.application.models.trace_context import TraceContextHolder
from app.application.execution.execution_context import ExecutionContext, ExecutionStatus
from app.engine.workflow_engine import WorkflowEngine
from app.engine.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class WorkflowDispatcher:
    """
    Workflow Dispatcher - Single orchestration gateway.
    
    DOCUMENT 07 APP-010
    """
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.orchestrator = Orchestrator()
    
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
        
        # Create ExecutionContext (APP-011)
        execution_context = ExecutionContext(
            company_id=company_id,
            user_id=user_id,
            dataset_id=dataset_id,
            objective_type=objective_type,
            params=params or {},
            trace_id=trace_context.trace_id if trace_context else None,
            correlation_id=trace_context.correlation_id if trace_context else None,
            request_id=trace_context.request_id if trace_context else None,
        )
        
        # Dispatch through workflow engine
        result = await self.workflow_engine.dispatch(execution_context)
        
        # Update trace context with execution_id
        if trace_context and result.get("execution_id"):
            trace_context.execution_id = result.get("execution_id")
        
        logger.info(
            f"✅ Business objective dispatched: {objective_type}",
            extra={
                "execution_id": str(result.get("execution_id")) if result.get("execution_id") else None,
                "trace_id": trace_context.trace_id if trace_context else None,
            }
        )
        
        return {
            "execution_id": result.get("execution_id"),
            "status": result.get("status", "started"),
            "message": f"Business objective '{objective_type}' started successfully",
            "trace_id": trace_context.trace_id if trace_context else None,
        }
    
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
        
        # Create ExecutionContext (APP-011)
        execution_context = ExecutionContext(
            company_id=company_id,
            user_id=user_id,
            dataset_id=dataset_id,
            analysis_type=analysis_type,
            material_codes=material_codes,
            params=params or {},
            trace_id=trace_context.trace_id if trace_context else None,
            correlation_id=trace_context.correlation_id if trace_context else None,
            request_id=trace_context.request_id if trace_context else None,
        )
        
        # Dispatch through workflow engine
        result = await self.workflow_engine.dispatch(execution_context)
        
        # Update trace context with execution_id
        if trace_context and result.get("execution_id"):
            trace_context.execution_id = result.get("execution_id")
        
        logger.info(
            f"✅ Single analysis dispatched: {analysis_type}",
            extra={
                "execution_id": str(result.get("execution_id")) if result.get("execution_id") else None,
                "trace_id": trace_context.trace_id if trace_context else None,
            }
        )
        
        return {
            "execution_id": result.get("execution_id"),
            "status": result.get("status", "started"),
            "message": f"Analysis '{analysis_type}' started successfully",
            "trace_id": trace_context.trace_id if trace_context else None,
        }
    
    async def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """
        Get execution status.
        """
        return await self.workflow_engine.get_status(execution_id)
    
    async def get_execution_result(self, execution_id: UUID) -> Dict[str, Any]:
        """
        Get execution result.
        """
        return await self.workflow_engine.get_result(execution_id)