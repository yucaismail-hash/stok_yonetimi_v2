# app/application/handlers/approve_dataset_handler.py
"""
Approve Dataset Handler - DOCUMENT 07 APP-009
Command Handler for dataset approval.
"""

import logging

from app.application.commands.base import ApproveDatasetCommand
from app.application.handlers.base import BaseHandler
from app.application.response.schemas import APIResponse
from app.application.validators.command_validator import CommandValidator
from app.services.dataset.dataset_service import DatasetService as DatasetProvider

logger = logging.getLogger(__name__)


class ApproveDatasetHandler(BaseHandler[ApproveDatasetCommand]):
    """
    Handler for ApproveDatasetCommand.
    """
    
    async def handle(self, command: ApproveDatasetCommand) -> APIResponse:
        """
        Handle ApproveDatasetCommand.
        """
        logger.info(
            f"✅ Handling ApproveDatasetCommand: {command.dataset_id}",
            extra={
                "company_id": str(command.company_id),
                "user_id": str(command.user_id),
                "dataset_id": str(command.dataset_id),
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
        
        # Approve dataset
        dataset_provider = DatasetProvider()
        approval_result = await dataset_provider.approve_dataset(
            company_id=command.company_id,
            user_id=command.user_id,
            dataset_id=command.dataset_id,
            notes=command.notes,
        )
        
        return self._success_response(
            data=approval_result,
            message="Dataset approved successfully",
        )
    
    def _validate_command(self, command: ApproveDatasetCommand) -> list:
        """Validate command."""
        errors = []
        
        # Validate common fields
        common_errors = CommandValidator.validate(command)
        errors.extend(common_errors)
        
        # Validate dataset_id
        if not command.dataset_id:
            errors.append({
                "field": "dataset_id",
                "message": "dataset_id is required",
                "code": "missing_field",
            })
        
        return errors