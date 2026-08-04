# app/engine/intelligence/models.py
"""
Execution Intelligence Models
DOCUMENT 04 - PART 05
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class DecisionType(str, Enum):
    """Types of execution decisions."""
    WORKFLOW_GENERATION = "workflow_generation"
    RULE_EVALUATION = "rule_evaluation"
    TASK_SCHEDULING = "task_scheduling"
    WORKER_ASSIGNMENT = "worker_assignment"
    CACHE_DECISION = "cache_decision"
    OPTIMIZATION = "optimization"
    FAILURE_HANDLING = "failure_handling"
    CANCELLATION = "cancellation"


class ExplanationLevel(str, Enum):
    """Level of explanation detail."""
    USER = "user"
    ADMIN = "admin"
    DEVELOPER = "developer"


@dataclass
class DecisionLog:
    """Execution Decision Log - DOCUMENT 04 Section 3"""
    decision_id: str
    workflow_id: str
    decision_type: DecisionType
    business_objective: str
    workflow_version: str
    rule_decisions: List[Dict[str, Any]]
    execution_plan: Dict[str, Any]
    skipped_tasks: List[str]
    conditional_tasks: List[Dict[str, Any]]
    optimization_decisions: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleDecisionLog:
    """Rule Engine Decision Log - DOCUMENT 04 Section 4"""
    rule_id: str
    rule_type: str
    reason: str
    decision: str
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExplanation:
    """Workflow explainability - DOCUMENT 04 Section 5"""
    workflow_id: str
    generation_reason: str
    skipped_tasks: List[Dict[str, str]]
    reordered_tasks: List[Dict[str, str]]
    parallel_execution_reason: str
    cache_decision: Dict[str, Any]
    stop_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    level: ExplanationLevel = ExplanationLevel.USER


@dataclass
class TaskExplanation:
    """Task explainability - DOCUMENT 04 Section 6"""
    task_id: str
    task_type: str
    execution_reason: str
    input_source: str
    output_destination: str
    dependency_status: str
    execution_duration_ms: Optional[float] = None
    worker_assignment: Optional[str] = None
    execution_result: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionMemory:
    """Execution Memory - DOCUMENT 04 Section 7"""
    memory_id: str
    workflow_pattern: Dict[str, Any]
    execution_characteristics: Dict[str, Any]
    rule_history: List[RuleDecisionLog]
    optimization_history: List[Dict[str, Any]]
    execution_statistics: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionLearning:
    """Execution Learning - DOCUMENT 04 Section 8"""
    workflow_id: str
    avg_duration_ms: Optional[float] = None
    avg_sku_processing_ms: Optional[float] = None
    avg_workflow_duration_ms: Optional[float] = None
    worker_performance: Dict[str, float] = field(default_factory=dict)
    cache_efficiency: float = 0.0
    failure_frequency: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    sample_count: int = 0


@dataclass
class ExecutionPrediction:
    """Execution Prediction - DOCUMENT 04 Section 9"""
    workflow_id: str
    expected_duration_ms: Optional[float] = None
    expected_resource_usage: Dict[str, float] = field(default_factory=dict)
    expected_worker_count: int = 1
    expected_cost: float = 0.0
    expected_queue_time_ms: Optional[float] = None
    confidence_score: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class HealthMetrics:
    """Health Monitoring - DOCUMENT 04 Section 11"""
    queue_length: int = 0
    worker_availability: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    execution_success_rate: float = 0.0
    retry_rate: float = 0.0
    failure_rate: float = 0.0
    avg_duration_ms: Optional[float] = None
    health_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionQuality:
    """Execution Quality - DOCUMENT 04 Section 12"""
    workflow_id: str
    correctness_score: float = 0.0
    completeness_score: float = 0.0
    reproducibility_score: float = 0.0
    stability_score: float = 0.0
    efficiency_score: float = 0.0
    overall_score: float = 0.0
    evaluated_at: datetime = field(default_factory=datetime.now)