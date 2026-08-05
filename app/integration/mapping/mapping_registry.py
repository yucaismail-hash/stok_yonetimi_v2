# app/integration/mapping/mapping_registry.py
"""
Mapping Registry - DOCUMENT 07 APP-028 / REVISION 05

New integrations SHALL register their mappings dynamically.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MappingRegistry:
    """
    Mapping Registry - Central registry for all integration mappings.
    
    New integrations SHALL register their mappings dynamically.
    """
    
    _instance = None
    _mappings: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(
        self,
        integration_type: str,
        mappings: Dict[str, Any],
        version: str = "1.0",
    ) -> None:
        """
        Register mappings for an integration type.
        
        Args:
            integration_type: Type of integration (e.g., "sap", "logo", "shopify")
            mappings: Field mappings
            version: Mapping version
        """
        self._mappings[integration_type] = {
            "mappings": mappings,
            "version": version,
        }
        logger.info(f"Registered mappings for integration: {integration_type}")
    
    def get_mappings(self, integration_type: str) -> Optional[Dict[str, Any]]:
        """Get mappings for an integration type."""
        if integration_type in self._mappings:
            return self._mappings[integration_type]["mappings"]
        return None
    
    def get_version(self, integration_type: str) -> Optional[str]:
        """Get mapping version for an integration type."""
        if integration_type in self._mappings:
            return self._mappings[integration_type]["version"]
        return None
    
    def list_integrations(self) -> list:
        """List all registered integrations."""
        return list(self._mappings.keys())
    
    def remove(self, integration_type: str) -> None:
        """Remove mappings for an integration type."""
        if integration_type in self._mappings:
            del self._mappings[integration_type]
            logger.info(f"Removed mappings for integration: {integration_type}")
    
    def clear(self) -> None:
        """Clear all mappings."""
        self._mappings.clear()
        logger.info("Cleared all mapping registrations")