# app/api/v2/contracts/contract_registry.py
"""
Contract Registry - DOCUMENT 07 APP-042 / REVISION 04

Every API Contract SHALL be registered centrally.
Future API versions SHALL reuse the same registry.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIContract:
    """API Contract definition."""
    version: str
    name: str
    description: str
    endpoints: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ContractRegistry:
    """
    Contract Registry - Central registry for API Contracts.
    
    Every API Contract SHALL be registered centrally.
    """
    
    _instance = None
    _contracts: Dict[str, APIContract] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, contract: APIContract) -> None:
        """Register an API Contract."""
        if contract.version in self._contracts:
            logger.warning(f"Contract already registered: {contract.version}")
        self._contracts[contract.version] = contract
        logger.info(f"Registered contract: {contract.version}")
    
    def get(self, version: str) -> Optional[APIContract]:
        """Get contract by version."""
        return self._contracts.get(version)
    
    def get_latest(self) -> Optional[APIContract]:
        """Get the latest contract version."""
        if not self._contracts:
            return None
        versions = sorted(self._contracts.keys())
        return self._contracts[versions[-1]]
    
    def list_versions(self) -> list:
        """List all contract versions."""
        return list(self._contracts.keys())
    
    def to_openapi(self, version: str) -> Dict[str, Any]:
        """Convert contract to OpenAPI specification."""
        contract = self.get(version)
        if not contract:
            return {}
        
        return {
            "openapi": "3.0.0",
            "info": {
                "title": contract.name,
                "description": contract.description,
                "version": contract.version,
            },
            "paths": contract.endpoints,
            "components": {
                "schemas": contract.schemas,
                "responses": contract.errors,
            },
        }


# Initialize default contract
def register_default_contract():
    """Register the default API contract."""
    registry = ContractRegistry()
    
    default_contract = APIContract(
        version="2.0",
        name="Stokonomi AI API",
        description="Stokonomi AI Platform API - Business capabilities",
        endpoints={
            "/objectives/run": {
                "method": "POST",
                "summary": "Run Business Objective",
                "request": {"$ref": "#/components/schemas/BusinessObjectiveRequest"},
                "response": {"$ref": "#/components/schemas/ExecutionResponse"},
            },
            "/analysis/run": {
                "method": "POST",
                "summary": "Run Single Analysis",
                "request": {"$ref": "#/components/schemas/SingleAnalysisRequest"},
                "response": {"$ref": "#/components/schemas/ExecutionResponse"},
            },
            "/datasets": {
                "method": "POST",
                "summary": "Upload Dataset",
                "request": {"$ref": "#/components/schemas/DatasetUploadRequest"},
                "response": {"$ref": "#/components/schemas/BaseResponse"},
            },
            "/executions/{id}": {
                "method": "GET",
                "summary": "Get Execution Status",
                "response": {"$ref": "#/components/schemas/BaseResponse"},
            },
            "/artifacts/{id}": {
                "method": "GET",
                "summary": "Get AI Artifact",
                "response": {"$ref": "#/components/schemas/ArtifactResponse"},
            },
        },
        schemas={
            "BusinessObjectiveRequest": {"type": "object", "properties": {}},
            "SingleAnalysisRequest": {"type": "object", "properties": {}},
            "ExecutionResponse": {"type": "object", "properties": {}},
            "ArtifactResponse": {"type": "object", "properties": {}},
            "BaseResponse": {"type": "object", "properties": {}},
        },
        errors={
            "AUTH-001": {"description": "Invalid Authentication Token"},
            "DATA-001": {"description": "Dataset Not Found"},
            "EXEC-001": {"description": "Execution Not Found"},
            "ART-001": {"description": "Artifact Not Found"},
            "SYS-001": {"description": "Unexpected Internal Error"},
        },
    )
    
    registry.register(default_contract)