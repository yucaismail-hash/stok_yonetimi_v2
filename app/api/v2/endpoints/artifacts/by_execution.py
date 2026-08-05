# app/api/v2/endpoints/artifacts/by_execution.py
"""
Artifact by Execution Endpoint - DOCUMENT 07 REVISION 01

GET /api/v2/artifacts/execution/{execution_id}

Analytical outputs SHALL always be retrieved through AI Artifacts.
Execution manages processes. AI Artifacts represent results.
"""

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.api.v2.schemas import ArtifactResponse
from app.api.v2.dependencies.auth import get_user_id
from app.api.v2.middleware.trace import TraceContextHolder
from app.application.services.artifact.artifact_service import ArtifactService

router = APIRouter(tags=["Artifacts"])


@router.get(
    "/execution/{execution_id}",
    response_model=ArtifactResponse,
    summary="Get Artifact by Execution",
    description="Get AI Artifact associated with an execution.",
)
async def get_artifact_by_execution(
    execution_id: UUID,
    user_id: UUID = Depends(get_user_id),
) -> ArtifactResponse:
    """
    Get AI Artifact by execution ID.
    
    Analytical outputs SHALL always be retrieved through AI Artifacts.
    Execution manages processes. AI Artifacts represent results.
    """
    # Get trace context
    trace_context = TraceContextHolder.get_context()
    
    # Execute through service
    service = ArtifactService()
    response = await service.get_artifact_by_execution(
        company_id=trace_context.company_id if trace_context else None,
        user_id=user_id,
        execution_id=execution_id,
        trace_id=trace_context.trace_id if trace_context else None,
        correlation_id=trace_context.correlation_id if trace_context else None,
    )
    
    return response