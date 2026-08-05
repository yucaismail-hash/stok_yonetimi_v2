# app/application/execution/execution_context.py
"""
Execution Context - DOCUMENT 07 APP-011
ExecutionContext SHALL become the official execution object.

Every analytical engine SHALL receive ExecutionContext only.

ExecutionContext SHALL contain:
- Execution ID
- Trace ID
- Correlation ID
- Company ID
- User ID
- Dataset ID
- Objective Type
- Analysis Type
- Parameters
- Created At
- Status
"""

from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """Execution status values."""
    PENDING = "pending"
    VALIDATING = "validating"
    EXECUTING = "executing"
    LEARNING = "learning"
    DECIDING = "deciding"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionObjectiveType(str, Enum):
    """Business objective types."""
    FORECAST = "forecast"
    SAFETY_STOCK = "safety_stock"
    SIMULATION = "simulation"
    SUPPLIER = "supplier"
    BACKTEST = "backtest"
    SEASONAL_ANALYSIS = "seasonal_analysis"
    TREND_ANALYSIS = "trend_analysis"


class ExecutionAnalysisType(str, Enum):
    """Single analysis types."""
    FORECAST = "forecast"
    SAFETY_STOCK = "safety_stock"
    SIMULATION = "simulation"
    SUPPLIER = "supplier"
    BACKTEST = "backtest"


@dataclass
class ExecutionContext:
    """
    Execution Context - DOCUMENT 07 APP-011
    
    Official execution object passed to analytical engines.
    Immutable after creation.
    """
    
    # Identifiers
    execution_id: UUID = field(default_factory=uuid4)
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Core
    company_id: UUID
    user_id: UUID
    dataset_id: UUID
    
    # Objective
    objective_type: Optional[str] = None
    analysis_type: Optional[str] = None
    material_codes: Optional[List[str]] = None
    
    # Configuration
    params: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Metadata
    workflow_id: Optional[str] = None
    prompt_version: Optional[str] = None
    narrative_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": str(self.execution_id),
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "company_id": str(self.company_id),
            "user_id": str(self.user_id),
            "dataset_id": str(self.dataset_id),
            "objective_type": self.objective_type,
            "analysis_type": self.analysis_type,
            "material_codes": self.material_codes,
            "params": self.params,
            "config": self.config,
            "status": self.status.value if self.status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "workflow_id": self.workflow_id,
            "prompt_version": self.prompt_version,
            "narrative_version": self.narrative_version,
        }
    
    def with_status(self, status: ExecutionStatus) -> "ExecutionContext":
        """Create a new context with updated status."""
        return ExecutionContext(
            execution_id=self.execution_id,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
            request_id=self.request_id,
            company_id=self.company_id,
            user_id=self.user_id,
            dataset_id=self.dataset_id,
            objective_type=self.objective_type,
            analysis_type=self.analysis_type,
            material_codes=self.material_codes,
            params=self.params,
            config=self.config,
            status=status,
            started_at=self.started_at,
            completed_at=datetime.utcnow() if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED] else None,
            workflow_id=self.workflow_id,
            prompt_version=self.prompt_version,
            narrative_version=self.narrative_version,
        )
    
    def with_workflow_id(self, workflow_id: str) -> "ExecutionContext":
        """Create a new context with workflow_id set."""
        return ExecutionContext(
            execution_id=self.execution_id,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
            request_id=self.request_id,
            company_id=self.company_id,
            user_id=self.user_id,
            dataset_id=self.dataset_id,
            objective_type=self.objective_type,
            analysis_type=self.analysis_type,
            material_codes=self.material_codes,
            params=self.params,
            config=self.config,
            status=self.status,
            started_at=self.started_at,
            completed_at=self.completed_at,
            workflow_id=workflow_id,
            prompt_version=self.prompt_version,
            narrative_version=self.narrative_version,
        )