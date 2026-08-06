# app/api/v2/endpoints/objectives/run.py
"""
Objectives Endpoint - DOCUMENT 07 APP-015 / APP-016

POST /api/v2/objectives/run

Business capabilities instead of analytical engines.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from uuid import UUID

from app.api.v2.schemas import BusinessObjectiveRequest, ExecutionResponse
from app.api.v2.dependencies.auth import get_user_id
from app.api.v2.dependencies.idempotency import IdempotencyKey
from app.api.v2.middleware.trace import TraceContextHolder
from app.application.services.objective.business_objective_service import BusinessObjectiveService
from app.application.mapping.command_mapper import CommandMapper

router = APIRouter(tags=["Objectives"])


@router.post(
    "/run",
    response_model=ExecutionResponse,
    status_code=202,
    summary="Run Business Objective",
    description="Run a business objective. Workflow Engine determines required analytical engines.",
)
async def run_objective(
    request: BusinessObjectiveRequest,
    user_id: UUID = Depends(get_user_id),
    idempotency_key: Optional[str] = Depends(IdempotencyKey),
) -> ExecutionResponse:
    """
    Run a business objective.
    
    Business Objective executions SHALL NOT specify analytical engines.
    Workflow Engine SHALL determine which engines are required.
    
    Examples:
    - Reduce Stockout → Forecast + Safety Stock + Supplier Analysis
    - Optimize Inventory → Forecast + Safety Stock + Simulation
    - Cost Reduction → Supplier Analysis + Backtest
    """
    # Get trace context
    trace_context = TraceContextHolder.get_context()
    
    # Map request to command
    command = CommandMapper.to_business_objective_command(
        request=request,
        user_id=user_id,
        trace_id=trace_context.trace_id if trace_context else None,
        correlation_id=trace_context.correlation_id if trace_context else None,
    )
    
    # Execute through service
    service = BusinessObjectiveService()
    response = await service.run_objective(
        company_id=command.company_id,
        user_id=command.user_id,
        dataset_id=command.dataset_id,
        objective_type=command.objective_type,
        params=command.params,
        trace_id=command.trace_id,
        correlation_id=command.correlation_id,
    )
    
    return response
