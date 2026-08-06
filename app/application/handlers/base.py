# app/application/handlers/base.py
"""
Base Command Handler - DOCUMENT 07 REVISION 03
Command Handlers SHALL become responsible for:
- Command execution
- Workflow preparation
- Transaction coordination
- Service invocation
"""

from typing import Optional, Any, Dict, TypeVar, Generic
from uuid import UUID
from abc import ABC, abstractmethod

from app.application.commands.base import BaseCommand
from app.application.response.response_builder import ResponseBuilder
from app.application.response.schemas import APIResponse
from app.application.models.trace_context import TraceContextHolder

CommandType = TypeVar('CommandType', bound=BaseCommand)


class BaseHandler(ABC, Generic[CommandType]):
    """
    Base Command Handler.
    
    Application Services SHALL NOT execute commands directly.
    Command Handlers SHALL become responsible for command execution.
    """
    
    @abstractmethod
    async def handle(self, command: CommandType) -> APIResponse:
        """
        Handle the command and return a response.
        """
        pass
    
    def _get_trace_context(self) -> Optional[dict]:
        """Get current trace context."""
        context = TraceContextHolder.get_context()
        if context:
            return context.to_dict()
        return None
    
    def _success_response(
        self,
        data: Any = None,
        message: str = "Success",
        execution_id: Optional[UUID] = None,
    ) -> APIResponse:
        """Build a success response."""
        return ResponseBuilder.success(
            data=data,
            message=message,
            execution_id=execution_id,
        )
    
    def _error_response(
        self,
        message: str = "An error occurred",
        errors: Optional[list] = None,
        execution_id: Optional[UUID] = None,
    ) -> APIResponse:
        """Build an error response."""
        return ResponseBuilder.error(
            message=message,
            errors=errors,
            execution_id=execution_id,
        )
