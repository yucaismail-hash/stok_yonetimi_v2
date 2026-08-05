# app/integration/mapping/mapping_engine.py
"""
Mapping Engine - DOCUMENT 07 APP-028 / REVISION 05

Orchestrates field mapping for all integrations.
"""

from typing import Dict, Any, Optional
import logging

from app.integration.mapping.field_mapper import FieldMapper
from app.integration.mapping.mapping_registry import MappingRegistry

logger = logging.getLogger(__name__)


class MappingEngine:
    """
    Mapping Engine - Orchestrates field mapping.
    
    Uses MappingRegistry for configuration and FieldMapper for execution.
    """
    
    def __init__(self):
        self.registry = MappingRegistry()
        self._mappers: Dict[str, FieldMapper] = {}
    
    def get_mapper(self, integration_type: str) -> Optional[FieldMapper]:
        """Get or create a FieldMapper for an integration type."""
        if integration_type in self._mappers:
            return self._mappers[integration_type]
        
        mappings = self.registry.get_mappings(integration_type)
        if not mappings:
            logger.warning(f"No mappings found for integration: {integration_type}")
            return None
        
        mapper = FieldMapper()
        mapper.add_mappings(mappings)
        self._mappers[integration_type] = mapper
        
        return mapper
    
    def map_record(
        self,
        integration_type: str,
        record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Map a record using the specified integration's mappings.
        """
        mapper = self.get_mapper(integration_type)
        if not mapper:
            return record
        
        return mapper.map_record(record)
    
    def map_records(
        self,
        integration_type: str,
        records: list,
    ) -> list:
        """
        Map multiple records using the specified integration's mappings.
        """
        mapper = self.get_mapper(integration_type)
        if not mapper:
            return records
        
        return mapper.map_records(records)
    
    def reverse_map(
        self,
        integration_type: str,
        internal_field: str,
    ) -> Optional[str]:
        """
        Reverse map internal field to external field.
        """
        mapper = self.get_mapper(integration_type)
        if not mapper:
            return None
        
        return mapper.reverse_map(internal_field)