# app/application/handlers/run_single_analysis_handler.py
"""
Run Single Analysis Handler - DOCUMENT 07 APP-014
Command Handler for single analysis execution.

Single Analysis requests SHALL also use Workflow Dispatcher.
The execution flow SHALL remain identical to business objectives.
"""

from typing import Dict, Any
import logging

from app.application.commands.base import RunSingleAnalysisCommand
from app.application.handlers.base import BaseHandler
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.application.response.schemas import APIResponse
from app.application.validators.command_validator import CommandValidator

logger = logging.getLogger(__name__)


class RunSingleAnalysisHandler(BaseHandler[RunSingleAnalysisCommand]):
    """
    Handler for RunSingleAnalysisCommand.
    
    Single Analysis requests SHALL use Workflow Dispatcher.
    Workflow Engine SHALL determine which analytical engines are required.
    """
    
    VALID_ANALYSIS_TYPES = [
        "forecast",
        "safety_stock",
        "simulation",
        "supplier",
        "backtest",
    ]
    
    def __init__(self):
        self.dispatcher = WorkflowDispatcher()
    
    async def handle(self, command: RunSingleAnalysisCommand) -> APIResponse:
        """
        Handle RunSingleAnalysisCommand.
        
        Steps:
        1. Validate command
        2. Dispatch workflow
        3. Return response
        """
        logger.info(
            f"⚡ Handling RunSingleAnalysisCommand: {command.analysis_type}",
            extra={
                "company_id": str(command.company_id),
                "user_id": str(command.user_id),
                "dataset_id": str(command.dataset_id),
                "analysis_type": command.analysis_type,
                "trace_id": command.trace_id,
            }
        )
        
        # 1. Validate command
        errors = self._validate_command(command)
        if errors:
            return self._error_response(
                message="Validation failed",
                errors=errors,
            )
        
        # 2. Dispatch workflow
        result = await self.dispatcher.dispatch_single_analysis(
            company_id=command.company_id,
            user_id=command.user_id,
            dataset_id=command.dataset_id,
            analysis_type=command.analysis_type,
            material_codes=command.material_codes,
            params=command.params,
        )
        
        # 3. Return response
        return self._success_response(
            data={
                "execution_id": str(result.get("execution_id")) if result.get("execution_id") else None,
                "status": result.get("status"),
                "message": result.get("message"),
            },
            message=f"Analysis '{command.analysis_type}' started successfully",
            execution_id=result.get("execution_id"),
        )
    
    def _validate_command(self, command: RunSingleAnalysisCommand) -> list:
        """Validate command."""
        errors = []
        
        # Validate common fields
        common_errors = CommandValidator.validate(command)
        errors.extend(common_errors)
        
        # Validate analysis_type
        if not command.analysis_type:
            errors.append({
                "field": "analysis_type",
                "message": "analysis_type is required",
                "code": "missing_field",
            })
        elif command.analysis_type not in self.VALID_ANALYSIS_TYPES:
            errors.append({
                "field": "analysis_type",
                "message": f"analysis_type must be one of: {', '.join(self.VALID_ANALYSIS_TYPES)}",
                "code": "invalid_value",
            })
        
        # Validate dataset_id
        if not command.dataset_id:
            errors.append({
                "field": "dataset_id",
                "message": "dataset_id is required",
                "code": "missing_field",
            })
        
        return errors