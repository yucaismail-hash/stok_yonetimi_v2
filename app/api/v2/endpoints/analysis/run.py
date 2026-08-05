# app/api/v2/endpoints/analysis/run.py
"""
Analysis Endpoint - DOCUMENT 07 APP-015 / APP-016

POST /api/v2/analysis/run

Single analysis execution through Workflow Dispatcher.
"""

from fastapi import APIRouter, Depends
from typing import Optional
from uuid import UUID

from app.api.v2.schemas import SingleAnalysisRequest, ExecutionResponse
from app.api.v2.dependencies.auth import get_user_id
from app.api.v2.dependencies.idempotency import IdempotencyKey
from app.api.v2.middleware.trace import TraceContextHolder
from app.application.services.execution.execution_service import ExecutionService
from app.application.mapping.command_mapper import CommandMapper

router = APIRouter(tags=["Analysis"])


@router.post(
    "/run",
    response_model=ExecutionResponse,
    status_code=202,
    summary="Run Single Analysis",
    description="Run a single analysis. The execution flow SHALL remain identical to business objectives.",
)
async def run_analysis(
    request: SingleAnalysisRequest,
    user_id: UUID = Depends(get_user_id),
    idempotency_key: Optional[str] = Depends(IdempotencyKey),
) -> ExecutionResponse:
    """
    Run a single analysis.
    
    Single Analysis requests SHALL also use Workflow Dispatcher.
    The execution flow SHALL remain identical to business objectives.
    """
    # Get trace context
    trace_context = TraceContextHolder.get_context()
    
    # Map request to command
    command = CommandMapper.to_single_analysis_command(
        request=request,
        user_id=user_id,
        trace_id=trace_context.trace_id if trace_context else None,
        correlation_id=trace_context.correlation_id if trace_context else None,
    )
    
    # Execute through service
    service = ExecutionService()
    response = await service.run_analysis(
        company_id=command.company_id,
        user_id=command.user_id,
        dataset_id=command.dataset_id,
        analysis_type=command.analysis_type,
        material_codes=command.material_codes,
        params=command.params,
        trace_id=command.trace_id,
        correlation_id=command.correlation_id,
    )
    
    return response