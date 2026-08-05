# app/application/handlers/upload_dataset_handler.py
"""
Upload Dataset Handler - DOCUMENT 07 APP-009
Command Handler for dataset upload.
"""

import logging

from app.application.commands.base import UploadDatasetCommand
from app.application.handlers.base import BaseHandler
from app.application.response.schemas import APIResponse
from app.application.validators.command_validator import CommandValidator
from app.services.dataset.dataset_service import DatasetService as DatasetProvider

logger = logging.getLogger(__name__)


class UploadDatasetHandler(BaseHandler[UploadDatasetCommand]):
    """
    Handler for UploadDatasetCommand.
    """
    
    VALID_SOURCE_TYPES = ["excel", "csv", "api"]
    
    async def handle(self, command: UploadDatasetCommand) -> APIResponse:
        """
        Handle UploadDatasetCommand.
        """
        logger.info(
            f"📤 Handling UploadDatasetCommand: {command.source_type}",
            extra={
                "company_id": str(command.company_id),
                "user_id": str(command.user_id),
                "source_type": command.source_type,
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
        
        # Upload dataset
        dataset_provider = DatasetProvider()
        dataset = await dataset_provider.upload_dataset(
            company_id=command.company_id,
            user_id=command.user_id,
            source_type=command.source_type,
            file_content=command.file_content,
            source_name=command.source_name,
            metadata=command.metadata,
        )
        
        return self._success_response(
            data={
                "dataset_id": str(dataset.id) if dataset else None,
                "source_type": command.source_type,
                "source_name": command.source_name,
                "status": "uploaded",
            },
            message="Dataset uploaded successfully",
        )
    
    def _validate_command(self, command: UploadDatasetCommand) -> list:
        """Validate command."""
        errors = []
        
        # Validate common fields
        common_errors = CommandValidator.validate(command)
        errors.extend(common_errors)
        
        # Validate source_type
        if not command.source_type:
            errors.append({
                "field": "source_type",
                "message": "source_type is required",
                "code": "missing_field",
            })
        elif command.source_type not in self.VALID_SOURCE_TYPES:
            errors.append({
                "field": "source_type",
                "message": f"source_type must be one of: {', '.join(self.VALID_SOURCE_TYPES)}",
                "code": "invalid_value",
            })
        
        return errors