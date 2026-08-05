# app/integration/mapping/field_mapper.py
"""
Field Mapper - DOCUMENT 07 APP-028 / REVISION 05

Mappings SHALL become configurable.
The platform SHALL NEVER hardcode ERP field mappings.
"""

from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class FieldMapper:
    """
    Field Mapper - Maps external fields to internal fields.
    
    Mappings are configurable and can be registered dynamically.
    """
    
    def __init__(self, mappings: Optional[Dict[str, Any]] = None):
        self.mappings = mappings or {}
        self.transformers: Dict[str, Callable] = {}
    
    def add_mapping(self, external_field: str, internal_field: str, transformer: Optional[Callable] = None):
        """Add a field mapping."""
        self.mappings[external_field] = internal_field
        if transformer:
            self.transformers[external_field] = transformer
    
    def add_mappings(self, mappings: Dict[str, Any]):
        """Add multiple field mappings."""
        for external_field, mapping in mappings.items():
            if isinstance(mapping, dict):
                internal_field = mapping.get("field")
                transformer = mapping.get("transformer")
            else:
                internal_field = mapping
                transformer = None
            
            self.add_mapping(external_field, internal_field, transformer)
    
    def map_field(self, external_field: str, value: Any) -> Any:
        """Map a single field."""
        internal_field = self.mappings.get(external_field, external_field)
        
        # Apply transformer if exists
        if external_field in self.transformers:
            return self.transformers[external_field](value)
        
        return value
    
    def map_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a record."""
        result = {}
        
        for external_field, value in record.items():
            internal_field = self.mappings.get(external_field, external_field)
            
            # Skip if internal field is None
            if internal_field is None:
                continue
            
            # Apply transformer if exists
            if external_field in self.transformers:
                result[internal_field] = self.transformers[external_field](value)
            else:
                result[internal_field] = value
        
        return result
    
    def map_records(self, records: list) -> list:
        """Map multiple records."""
        return [self.map_record(record) for record in records]
    
    def reverse_map(self, internal_field: str) -> Optional[str]:
        """Reverse map internal field to external field."""
        for external, internal in self.mappings.items():
            if internal == internal_field:
                return external
        return None