# app/integration/adapters/erp_adapter.py
"""
Generic ERP Adapter - DOCUMENT 07 APP-025 / REVISION 01

Generic ERP Integration Adapter.
Vendor specific implementations SHALL be developed only when actual integrations are required.
The platform core SHALL remain completely independent from any ERP vendor.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID

from app.integration.adapters.base_adapter import BaseAdapter
from app.application.commands.base import (
    BaseCommand,
    RunBusinessObjectiveCommand,
    RunSingleAnalysisCommand,
    UploadDatasetCommand,
)
from app.application.response.schemas import APIResponse


class ERPAdapter(BaseAdapter):
    """
    Generic ERP Integration Adapter.
    
    Supports common ERP integration patterns.
    Vendor-specific mappings SHALL be configured dynamically.
    """
    
    adapter_type = "erp"
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        mapping_registry: Optional[Dict[str, str]] = None,
    ):
        super().__init__(config)
        self.mapping_registry = mapping_registry or {}
    
    async def validate_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate ERP payload."""
        # Check required fields based on operation type
        operation = payload.get("operation")
        
        if operation == "import_dataset":
            required = ["data", "source_type"]
        elif operation == "run_objective":
            required = ["objective_type", "dataset_id"]
        elif operation == "run_analysis":
            required = ["analysis_type", "dataset_id"]
        else:
            return False
        
        return all(field in payload for field in required)
    
    async def transform_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform ERP payload to internal format."""
        operation = payload.get("operation")
        transformed = {
            "operation": operation,
            "company_id": self.config.get("company_id"),
            "user_id": self.config.get("user_id"),
        }
        
        if operation == "import_dataset":
            transformed.update({
                "source_type": payload.get("source_type", "erp"),
                "source_name": payload.get("source_name", "ERP Import"),
                "data": payload.get("data"),
            })
        elif operation == "run_objective":
            transformed.update({
                "objective_type": payload.get("objective_type"),
                "dataset_id": payload.get("dataset_id"),
                "params": payload.get("params", {}),
            })
        elif operation == "run_analysis":
            transformed.update({
                "analysis_type": payload.get("analysis_type"),
                "dataset_id": payload.get("dataset_id"),
                "material_codes": payload.get("material_codes"),
                "params": payload.get("params", {}),
            })
        
        return transformed
    
    async def create_command(self, transformed: Dict[str, Any]) -> BaseCommand:
        """Create Application Command from transformed data."""
        operation = transformed.get("operation")
        
        if operation == "import_dataset":
            return UploadDatasetCommand(
                user_id=transformed["user_id"],
                company_id=transformed["company_id"],
                source_type=transformed["source_type"],
                source_name=transformed["source_name"],
                file_content=transformed.get("data"),
                metadata={"source": "erp"},
            )
        elif operation == "run_objective":
            return RunBusinessObjectiveCommand(
                user_id=transformed["user_id"],
                company_id=transformed["company_id"],
                objective_type=transformed["objective_type"],
                dataset_id=UUID(transformed["dataset_id"]),
                params=transformed["params"],
            )
        elif operation == "run_analysis":
            return RunSingleAnalysisCommand(
                user_id=transformed["user_id"],
                company_id=transformed["company_id"],
                analysis_type=transformed["analysis_type"],
                dataset_id=UUID(transformed["dataset_id"]),
                material_codes=transformed.get("material_codes"),
                params=transformed["params"],
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def format_response(self, result: APIResponse) -> Dict[str, Any]:
        """Format internal response for ERP."""
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "metadata": {
                "execution_id": str(result.metadata.execution_id) if result.metadata.execution_id else None,
                "trace_id": result.metadata.trace_id,
                "timestamp": result.metadata.timestamp.isoformat() if result.metadata.timestamp else None,
            }
        }
    
    async def execute_command(self, command: BaseCommand) -> APIResponse:
        """Execute Application Command."""
        # This would be implemented to call the Application Layer
        # For now, return a placeholder
        return APIResponse(
            success=True,
            message="Command executed successfully",
            data={"status": "pending"},
            metadata={}
        )