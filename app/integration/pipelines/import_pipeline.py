# app/integration/pipelines/import_pipeline.py
"""
Import Pipeline - DOCUMENT 07 REVISION 02 / REVISION 03

ImportPipeline SHALL orchestrate:
1. Validation
2. Transformation
3. Normalization
4. Field Mapping
5. Application Command Creation
6. Application Layer

Import strategies SHALL become small reusable components.
"""

from typing import Optional, Dict, Any, Type
import logging

from app.integration.adapters.base_adapter import BaseAdapter
from app.integration.mapping.mapping_engine import MappingEngine
from app.integration.errors.error_handler import ErrorHandler
from app.application.commands.base import BaseCommand
from app.application.response.schemas import APIResponse

logger = logging.getLogger(__name__)


class ImportPipeline:
    """
    Import Pipeline - Orchestrates import workflows.
    
    Every import strategy SHALL reuse ImportPipeline.
    """
    
    def __init__(self, adapter: BaseAdapter):
        self.adapter = adapter
        self.mapping_engine = MappingEngine()
        self.error_handler = ErrorHandler()
    
    async def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process import through the pipeline.
        
        Pipeline:
        1. Validate
        2. Transform
        3. Normalize
        4. Map Fields
        5. Create Command
        6. Execute
        """
        try:
            # 1. Validate
            is_valid = await self.adapter.validate_payload(payload)
            if not is_valid:
                return {
                    "success": False,
                    "error": {
                        "code": "validation_failed",
                        "message": "Payload validation failed",
                    }
                }
            
            # 2. Transform
            transformed = await self.adapter.transform_payload(payload)
            
            # 3. Normalize (if needed)
            normalized = self._normalize(transformed)
            
            # 4. Map Fields
            integration_type = payload.get("integration_type", "default")
            mapped = self.mapping_engine.map_record(integration_type, normalized)
            
            # 5. Create Command
            command = await self.adapter.create_command(mapped)
            
            # 6. Execute
            result = await self.adapter.execute_command(command)
            
            return await self.adapter.format_response(result)
            
        except Exception as e:
            return self.error_handler.handle(e, {"pipeline": "import"})
    
    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize data.
        
        This is a placeholder for actual normalization logic.
        """
        # Apply standard normalization rules
        normalized = {}
        for key, value in data.items():
            # Convert string keys to snake_case
            normalized_key = self._to_snake_case(key)
            normalized[normalized_key] = value
        return normalized
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()