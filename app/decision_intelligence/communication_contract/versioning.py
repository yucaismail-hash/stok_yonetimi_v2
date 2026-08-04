# app/decision_intelligence/communication_contract/versioning.py
"""
Communication Versioning - DOCUMENT 06 - PART 05
"""

from typing import Dict, Any
from datetime import datetime


class CommunicationVersioning:
    """
    Communication Versioning - CP-007
    
    Manages versioning for all communication artifacts.
    """
    
    CONTRACT_VERSION = "1.0.0"
    SCHEMA_VERSION = "2.0"
    
    @classmethod
    def add_version_metadata(cls, data: Dict[str, Any], prompt_version: str, model: str = "unknown") -> Dict[str, Any]:
        """Add version metadata to communication output."""
        data["_version"] = {
            "contract_version": cls.CONTRACT_VERSION,
            "schema_version": cls.SCHEMA_VERSION,
            "prompt_version": prompt_version,
            "llm_model": model,
            "generated_at": datetime.now().isoformat(),
        }
        return data
    
    @classmethod
    def get_version_info(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get version information from data."""
        return data.get("_version", {
            "contract_version": "unknown",
            "schema_version": "unknown",
            "prompt_version": "unknown",
            "llm_model": "unknown",
            "generated_at": None,
        })
    
    @classmethod
    def is_compatible(cls, version_info: Dict[str, Any]) -> bool:
        """Check if version is compatible with current version."""
        schema_version = version_info.get("schema_version", "1.0")
        return schema_version == cls.SCHEMA_VERSION
    
    @classmethod
    def get_traceability_info(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get traceability information."""
        version_info = cls.get_version_info(data)
        return {
            "prompt_version": version_info.get("prompt_version"),
            "contract_version": version_info.get("contract_version"),
            "schema_version": version_info.get("schema_version"),
            "generated_at": version_info.get("generated_at"),
            "is_compatible": cls.is_compatible(version_info),
        }