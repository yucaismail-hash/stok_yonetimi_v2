# app/application/handlers/retrieve_artifact_handler.py
"""
Retrieve Artifact Handler - DOCUMENT 07 APP-009
Command Handler for artifact retrieval.
"""

import logging

from app.application.commands.base import RetrieveArtifactCommand
from app.application.handlers.base import BaseHandler
from app.application.response.schemas import APIResponse
from app.application.validators.command_validator import CommandValidator
from app.decision_intelligence.decision_intelligence_engine import DecisionIntelligenceEngine

logger = logging.getLogger(__name__)


class RetrieveArtifactHandler(BaseHandler[RetrieveArtifactCommand]):
    """
    Handler for RetrieveArtifactCommand.
    """
    
    def __init__(self):
        self.engine = DecisionIntelligenceEngine()
    
    async def handle(self, command: RetrieveArtifactCommand) -> APIResponse:
        """
        Handle RetrieveArtifactCommand.
        """
        logger.info(
            f"📄 Handling RetrieveArtifactCommand",
            extra={
                "company_id": str(command.company_id),
                "user_id": str(command.user_id),
                "artifact_id": str(command.artifact_id) if command.artifact_id else None,
                "execution_id": str(command.execution_id) if command.execution_id else None,
                "trace_id": command.trace_id,
            }
        )
        
        # Validate command
        errors = self._validate_command(command)
        if errors:
            return self._error_response(
                message="Validation failed",
                errors=errors,
            )
        
        # Retrieve artifact
        if command.artifact_id:
            artifact = self.engine.get_artifact(str(command.artifact_id))
        elif command.execution_id:
            artifact = self.engine.get_artifact_by_execution(command.execution_id)
        else:
            return self._error_response(
                message="Either artifact_id or execution_id is required",
                errors=[{
                    "field": "artifact_id",
                    "message": "Either artifact_id or execution_id is required",
                    "code": "missing_field",
                }],
            )
        
        if not artifact:
            return self._error_response(
                message="Artifact not found",
                errors=[{
                    "field": "artifact_id",
                    "message": "Artifact not found",
                    "code": "not_found",
                }],
            )
        
        return self._success_response(
            data=artifact,
            message="Artifact retrieved successfully",
        )
    
    def _validate_command(self, command: RetrieveArtifactCommand) -> list:
        """Validate command."""
        errors = []
        
        # Validate common fields
        common_errors = CommandValidator.validate(command)
        errors.extend(common_errors)
        
        # Validate at least one identifier
        if not command.artifact_id and not command.execution_id:
            errors.append({
                "field": "identifier",
                "message": "Either artifact_id or execution_id is required",
                "code": "missing_field",
            })
        
        return errors