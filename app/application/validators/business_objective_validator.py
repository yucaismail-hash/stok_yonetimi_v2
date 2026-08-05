# app/application/validators/business_objective_validator.py
"""
Business Objective Validator - DOCUMENT 07 APP-013
Validates business objective commands.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from app.application.commands.run_business_objective import RunBusinessObjectiveCommand
from app.application.validators.command_validator import CommandValidator


class BusinessObjectiveValidator:
    """
    Validator for RunBusinessObjectiveCommand.
    
    Business Objective executions SHALL NOT specify analytical engines.
    Workflow Engine SHALL determine which engines are required.
    """
    
    VALID_OBJECTIVE_TYPES = [
        "forecast",
        "safety_stock",
        "simulation",
        "supplier",
        "backtest",
        "seasonal_analysis",
        "trend_analysis",
    ]
    
    @classmethod
    def validate(cls, command: RunBusinessObjectiveCommand) -> List[Dict[str, Any]]:
        """
        Validate RunBusinessObjectiveCommand.
        """
        errors = []
        
        # Validate common fields
        common_errors = CommandValidator.validate(command)
        errors.extend(common_errors)
        
        # Validate objective_type
        if not command.objective_type:
            errors.append({
                "field": "objective_type",
                "message": "objective_type is required",
                "code": "missing_field",
            })
        elif command.objective_type not in cls.VALID_OBJECTIVE_TYPES:
            errors.append({
                "field": "objective_type",
                "message": f"objective_type must be one of: {', '.join(cls.VALID_OBJECTIVE_TYPES)}",
                "code": "invalid_value",
            })
        
        # Validate dataset_id
        if not command.dataset_id:
            errors.append({
                "field": "dataset_id",
                "message": "dataset_id is required",
                "code": "missing_field",
            })
        
        return errors