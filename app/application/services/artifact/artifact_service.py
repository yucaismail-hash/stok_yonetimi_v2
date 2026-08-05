# app/application/services/artifact/artifact_service.py
"""
Artifact Service - DOCUMENT 07 REVISION 02
Domain-based application service for AI Artifact operations.

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

from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

from app.application.commands.base import RetrieveArtifactCommand
from app.application.handlers.retrieve_artifact_handler import RetrieveArtifactHandler
from app.application.response.schemas import APIResponse, ResponseBuilder

logger = logging.getLogger(__name__)


class ArtifactService:
    """
    Artifact Service - Domain-based application service.
    
    Responsible for AI Artifact orchestration.
    """
    
    def __init__(self):
        self.retrieve_handler = RetrieveArtifactHandler()
    
    async def get_artifact(
        self,
        company_id: UUID,
        user_id: UUID,
        artifact_id: UUID,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Get an AI Artifact by ID.
        
        Args:
            company_id: Company ID
            user_id: User ID
            artifact_id: Artifact ID
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with artifact
        """
        logger.info(
            f"📄 ArtifactService.get_artifact: {artifact_id}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "artifact_id": str(artifact_id),
            }
        )
        
        # Create command
        command = RetrieveArtifactCommand(
            user_id=user_id,
            company_id=company_id,
            artifact_id=artifact_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        
        # Execute through handler
        return await self.retrieve_handler.handle(command)
    
    async def get_artifact_by_execution(
        self,
        company_id: UUID,
        user_id: UUID,
        execution_id: UUID,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Get an AI Artifact by execution ID.
        
        Args:
            company_id: Company ID
            user_id: User ID
            execution_id: Execution ID
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with artifact
        """
        logger.info(
            f"📄 ArtifactService.get_artifact_by_execution: {execution_id}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "execution_id": str(execution_id),
            }
        )
        
        # Create command
        command = RetrieveArtifactCommand(
            user_id=user_id,
            company_id=company_id,
            execution_id=execution_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        
        # Execute through handler
        return await self.retrieve_handler.handle(command)
    
    async def list_artifacts(
        self,
        company_id: UUID,
        user_id: UUID,
        artifact_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        List AI Artifacts.
        
        Args:
            company_id: Company ID
            user_id: User ID
            artifact_type: Optional artifact type filter
            limit: Limit
            offset: Offset
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with artifacts list
        """
        logger.info(
            f"📄 ArtifactService.list_artifacts",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "artifact_type": artifact_type,
                "limit": limit,
                "offset": offset,
            }
        )
        
        # Import decision intelligence engine
        from app.decision_intelligence.decision_intelligence_engine import DecisionIntelligenceEngine
        
        engine = DecisionIntelligenceEngine()
        artifacts = engine.list_artifacts(
            company_id=company_id,
            artifact_type=artifact_type,
            limit=limit,
            offset=offset,
        )
        
        return ResponseBuilder.success(
            data={
                "items": artifacts,
                "total": len(artifacts),
                "limit": limit,
                "offset": offset,
            },
            message="Artifacts retrieved successfully",
        )