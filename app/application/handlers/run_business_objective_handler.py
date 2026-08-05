# app/application/handlers/run_business_objective_handler.py
"""
Run Business Objective Handler - DOCUMENT 07 REVISION 03
Command Handler for business objective execution.

Command Handlers SHALL become responsible for:
- Command execution
- Workflow preparation
- Transaction coordination
- Service invocation
"""

from typing import Dict, Any
import logging

from app.application.commands.base import RunBusinessObjectiveCommand
from app.application.handlers.base import BaseHandler
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.application.response.schemas import APIResponse

logger = logging.getLogger(__name__)


class RunBusinessObjectiveHandler(BaseHandler[RunBusinessObjectiveCommand]):
    """
    Handler for RunBusinessObjectiveCommand.
    """
    
    def __init__(self):
        self.dispatcher = WorkflowDispatcher()
    
    async def handle(self, command: RunBusinessObjectiveCommand) -> APIResponse:
        """
        Handle RunBusinessObjectiveCommand.
        
        Steps:
        1. Validate command
        2. Dispatch workflow
        3. Return response
        """
        logger.info(
            f"🎯 Handling RunBusinessObjectiveCommand: {command.objective_type}",
            extra={
                "company_id": str(command.company_id),
                "user_id": str(command.user_id),
                "dataset_id": str(command.dataset_id),
                "objective_type": command.objective_type,
                "trace_id": command.trace_id,
            }
        )
        
        # 1. Validate command
        self._validate_command(command)
        
        # 2. Dispatch workflow
        result = await self.dispatcher.dispatch_business_objective(
            company_id=command.company_id,
            user_id=command.user_id,
            dataset_id=command.dataset_id,
            objective_type=command.objective_type,
            params=command.params,
        )
        
        # 3. Return response
        return self._success_response(
            data={
                "execution_id": str(result.get("execution_id")) if result.get("execution_id") else None,
                "status": result.get("status"),
                "message": result.get("message"),
            },
            message=f"Business objective '{command.objective_type}' started successfully",
            execution_id=result.get("execution_id"),
        )
    
    def _validate_command(self, command: RunBusinessObjectiveCommand) -> None:
        """Validate command."""
        if not command.objective_type:
            raise ValueError("objective_type is required")
        if not command.dataset_id:
            raise ValueError("dataset_id is required")