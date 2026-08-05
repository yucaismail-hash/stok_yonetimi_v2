# app/api/v2/endpoints/executions/status.py
"""
Execution Status Endpoint - DOCUMENT 07 APP-020

GET /api/v2/executions/{id}

Execution resources SHALL expose:
- Execution State
- Execution Progress
- Current Stage
- Worker Status
- Estimated Completion

Execution resources SHALL NEVER return analytical results.
"""

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.api.v2.schemas import BaseResponse
from app.api.v2.dependencies.auth import get_user_id
from app.api.v2.middleware.trace import TraceContextHolder
from app.application.services.execution.execution_service import ExecutionService

router = APIRouter(tags=["Executions"])


@router.get(
    "/{execution_id}",
    response_model=BaseResponse,
    summary="Get Execution Status",
    description="Get execution status and progress. Analytical results are not returned here.",
)
async def get_execution_status(
    execution_id: UUID,
    user_id: UUID = Depends(get_user_id),
) -> BaseResponse:
    """
    Get execution status.
    
    Execution resources SHALL expose:
    - Execution State
    - Execution Progress
    - Current Stage
    - Worker Status
    - Estimated Completion
    
    Execution resources SHALL NEVER return analytical results.
    """
    # Get trace context
    trace_context = TraceContextHolder.get_context()
    
    # Execute through service
    service = ExecutionService()
    response = await service.get_execution_status(
        execution_id=execution_id,
        trace_id=trace_context.trace_id if trace_context else None,
    )
    
    return response