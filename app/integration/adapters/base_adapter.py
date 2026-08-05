# app/integration/adapters/base_adapter.py
"""
Base Integration Adapter - DOCUMENT 07 APP-025 / REVISION 01

External systems SHALL communicate only with Integration Adapters.
Integration Adapters SHALL translate external requests into Application Commands.
Integration Adapters SHALL NEVER execute business logic.
Integration Adapters SHALL NEVER execute analytical calculations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TypeVar, Generic
from uuid import UUID

from app.application.commands.base import BaseCommand
from app.application.response.schemas import APIResponse
from app.integration.errors.error_handler import ErrorHandler

T = TypeVar('T')


class BaseAdapter(ABC, Generic[T]):
    """
    Base Integration Adapter.
    
    Every external platform SHALL implement an Integration Adapter.
    Integration Adapters SHALL remain independent from analytical engines.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.error_handler = ErrorHandler()
    
    @abstractmethod
    async def validate_payload(self, payload: T) -> bool:
        """
        Validate incoming payload.
        
        Integration Adapters SHALL validate payloads before processing.
        """
        pass
    
    @abstractmethod
    async def transform_payload(self, payload: T) -> Dict[str, Any]:
        """
        Transform external payload to internal format.
        """
        pass
    
    @abstractmethod
    async def create_command(self, transformed: Dict[str, Any]) -> BaseCommand:
        """
        Create Application Command from transformed data.
        """
        pass
    
    @abstractmethod
    async def format_response(self, result: APIResponse) -> Dict[str, Any]:
        """
        Format internal response for external system.
        """
        pass
    
    async def process(self, payload: T) -> Dict[str, Any]:
        """
        Process external request through integration pipeline.
        
        Integration Pipeline:
        1. Validate
        2. Transform
        3. Create Command
        4. Invoke Application Layer
        5. Format Response
        """
        try:
            # 1. Validate
            is_valid = await self.validate_payload(payload)
            if not is_valid:
                return {
                    "success": False,
                    "error": {
                        "code": "validation_failed",
                        "message": "Payload validation failed",
                    }
                }
            
            # 2. Transform
            transformed = await self.transform_payload(payload)
            
            # 3. Create Command
            command = await self.create_command(transformed)
            
            # 4. Invoke Application Layer (implemented by subclasses)
            result = await self.execute_command(command)
            
            # 5. Format Response
            return await self.format_response(result)
            
        except Exception as e:
            return self.error_handler.handle(e, {"adapter": self.__class__.__name__})
    
    @abstractmethod
    async def execute_command(self, command: BaseCommand) -> APIResponse:
        """
        Execute Application Command.
        
        Adapters SHALL communicate only with the Application Layer.
        """
        pass
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get adapter information."""
        return {
            "name": self.__class__.__name__,
            "type": self._get_adapter_type(),
            "version": "1.0",
        }
    
    def _get_adapter_type(self) -> str:
        """Get adapter type."""
        if hasattr(self, 'adapter_type'):
            return self.adapter_type
        return "generic"