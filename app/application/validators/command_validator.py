# app/application/validators/command_validator.py
"""
Command Validator - DOCUMENT 07 APP-008
Validates Application Commands before execution.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from app.application.commands.base import BaseCommand


class CommandValidator:
    """
    Validator for Application Commands.
    
    Commands SHALL contain:
    - Request Identifier
    - User Identifier
    - Company Identifier
    - Dataset Identifier
    - Business Objective
    - Requested Analysis
    - Execution Configuration
    - Timestamp
    """
    
    @classmethod
    def validate(cls, command: BaseCommand) -> List[Dict[str, Any]]:
        """
        Validate a command.
        
        Returns:
            List of validation errors. Empty list means valid.
        """
        errors = []
        
        # Validate common fields
        if not command.user_id:
            errors.append({
                "field": "user_id",
                "message": "user_id is required",
                "code": "missing_field",
            })
        
        if not command.company_id:
            errors.append({
                "field": "company_id",
                "message": "company_id is required",
                "code": "missing_field",
            })
        
        return errors
    
    @classmethod
    def validate_uuid(cls, value: Optional[UUID], field: str) -> Optional[List[Dict[str, Any]]]:
        """Validate UUID field."""
        if not value:
            return [{
                "field": field,
                "message": f"{field} is required",
                "code": "missing_field",
            }]
        return None
    
    @classmethod
    def validate_string(cls, value: Optional[str], field: str, max_length: int = 255) -> Optional[List[Dict[str, Any]]]:
        """Validate string field."""
        if not value:
            return [{
                "field": field,
                "message": f"{field} is required",
                "code": "missing_field",
            }]
        if len(value) > max_length:
            return [{
                "field": field,
                "message": f"{field} exceeds maximum length of {max_length}",
                "code": "too_long",
            }]
        return None
    
    @classmethod
    def validate_in_list(cls, value: str, field: str, allowed_values: List[str]) -> Optional[List[Dict[str, Any]]]:
        """Validate value is in allowed list."""
        if value not in allowed_values:
            return [{
                "field": field,
                "message": f"{field} must be one of: {', '.join(allowed_values)}",
                "code": "invalid_value",
            }]
        return None