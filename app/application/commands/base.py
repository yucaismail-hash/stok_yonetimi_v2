# app/application/commands/base.py
"""
Base Command - DOCUMENT 07 APP-003
Every incoming request SHALL become an Application Command.
"""

from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime


@dataclass
class BaseCommand:
    """
    Base Application Command.
    
    Every incoming request SHALL become an Application Command.
    Application Commands SHALL become the only communication objects
    exchanged between the Application Layer and Application Services.
    """
    
    user_id: UUID
    company_id: UUID
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary."""
        return {
            "user_id": str(self.user_id),
            "company_id": str(self.company_id),
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
        }


@dataclass
class RunBusinessObjectiveCommand(BaseCommand):
    """
    Command to run a business objective.
    
    Examples:
    - forecast
    - safety_stock
    - simulation
    - supplier
    - backtest
    """
    
    objective_type: str
    dataset_id: UUID
    params: Optional[Dict[str, Any]] = None


@dataclass
class RunSingleAnalysisCommand(BaseCommand):
    """
    Command to run a single analysis.
    """
    
    analysis_type: str  # forecast, safety_stock, simulation, supplier, backtest
    dataset_id: UUID
    material_codes: Optional[list[str]] = None
    params: Optional[Dict[str, Any]] = None


@dataclass
class UploadDatasetCommand(BaseCommand):
    """
    Command to upload a dataset.
    """
    
    source_type: str  # excel, csv, api
    source_name: Optional[str] = None
    file_content: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ValidateDatasetCommand(BaseCommand):
    """
    Command to validate a dataset.
    """
    
    dataset_id: UUID


@dataclass
class ApproveDatasetCommand(BaseCommand):
    """
    Command to approve a dataset.
    """
    
    dataset_id: UUID
    notes: Optional[str] = None


@dataclass
class RetrieveArtifactCommand(BaseCommand):
    """
    Command to retrieve an AI Artifact.
    """
    
    artifact_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    artifact_type: Optional[str] = None