# app/learning/learning_context.py
"""
Learning Context - DOCUMENT 05 - PART 01
Single runtime context object for the entire Learning Engine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


@dataclass
class LearningContext:
    """
    Learning Context - DOCUMENT 05
    
    Contains all information required during one learning cycle.
    Learning components receive LearningContext instead of many independent parameters.
    """
    
    # Company & User
    company_id: UUID
    user_id: UUID
    company_name: Optional[str] = field(default=None, kw_only=True)
    
    # Dataset
    dataset_id: UUID
    dataset_version: int
    dataset_hash: Optional[str] = field(default=None, kw_only=True)
    
    # Execution
    execution_id: UUID
    workflow_id: str
    business_objective: str
    workflow_version: str
    algorithm_version: str = "1.0.0"
    
    # Results
    simulation_results: Dict[str, Any] = field(default_factory=dict)
    backtest_results: Dict[str, Any] = field(default_factory=dict)
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # User Feedback
    user_feedback: Optional[Dict[str, Any]] = None
    user_rating: Optional[float] = None
    
    # External Intelligence
    external_intelligence: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    triggered_at: datetime = field(default_factory=datetime.now)
    learning_cycle_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "company_id": str(self.company_id),
            "user_id": str(self.user_id),
            "company_name": self.company_name,
            "dataset_id": str(self.dataset_id),
            "dataset_version": self.dataset_version,
            "dataset_hash": self.dataset_hash,
            "execution_id": str(self.execution_id),
            "workflow_id": self.workflow_id,
            "business_objective": self.business_objective,
            "workflow_version": self.workflow_version,
            "algorithm_version": self.algorithm_version,
            "simulation_results": self.simulation_results,
            "backtest_results": self.backtest_results,
            "execution_metrics": self.execution_metrics,
            "user_feedback": self.user_feedback,
            "user_rating": self.user_rating,
            "external_intelligence": self.external_intelligence,
            "triggered_at": self.triggered_at.isoformat(),
            "learning_cycle_id": self.learning_cycle_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningContext':
        """Create context from dictionary."""
        return cls(
            company_id=UUID(data["company_id"]),
            user_id=UUID(data["user_id"]),
            company_name=data.get("company_name"),
            dataset_id=UUID(data["dataset_id"]),
            dataset_version=data["dataset_version"],
            dataset_hash=data.get("dataset_hash"),
            execution_id=UUID(data["execution_id"]),
            workflow_id=data["workflow_id"],
            business_objective=data["business_objective"],
            workflow_version=data.get("workflow_version", "1.0.0"),
            algorithm_version=data.get("algorithm_version", "1.0.0"),
            simulation_results=data.get("simulation_results", {}),
            backtest_results=data.get("backtest_results", {}),
            execution_metrics=data.get("execution_metrics", {}),
            user_feedback=data.get("user_feedback"),
            user_rating=data.get("user_rating"),
            external_intelligence=data.get("external_intelligence", {}),
            triggered_at=datetime.fromisoformat(data["triggered_at"]) if "triggered_at" in data else datetime.now(),
            learning_cycle_id=data.get("learning_cycle_id"),
            metadata=data.get("metadata", {}),
        )
