# app/engine/enums.py
"""
Execution Engine Enums
DOCUMENT 04 - PART 01
"""

from enum import Enum, auto


class TaskType(str, Enum):
    """DOCUMENT 04 - Section 9: Task Types"""
    
    # Analytical Tasks
    FORECAST = "forecast"
    SAFETY_STOCK = "safety_stock"
    SIMULATION = "simulation"
    BACKTEST = "backtest"
    SUPPLIER = "supplier"
    
    # Learning Tasks
    COMPANY_LEARNING = "company_learning"
    PATTERN_INTELLIGENCE = "pattern_intelligence"
    DECISION_LEARNING = "decision_learning"
    
    # Validation Tasks
    DATASET_VALIDATION = "dataset_validation"
    
    # Notification Tasks
    NOTIFICATION = "notification"
    
    # Cache Tasks
    CACHE_UPDATE = "cache_update"
    CACHE_INVALIDATE = "cache_invalidate"
    
    # System Tasks
    SYSTEM = "system"


class ExecutionState(str, Enum):
    """DOCUMENT 04 - Section 10: Execution States"""
    
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    
    @classmethod
    def is_terminal(cls, state: str) -> bool:
        """Check if state is terminal (completed, failed, cancelled)."""
        return state in [cls.COMPLETED, cls.FAILED, cls.CANCELLED]
    
    @classmethod
    def is_active(cls, state: str) -> bool:
        """Check if state is active (running, waiting, retrying)."""
        return state in [cls.RUNNING, cls.WAITING, cls.RETRYING]


class BusinessObjective(str, Enum):
    """DOCUMENT 04 - Section 6: Business Objectives"""
    
    DEMAND_FORECAST = "demand_forecast"
    SAFETY_STOCK_OPTIMIZATION = "safety_stock_optimization"
    SUPPLIER_OPTIMIZATION = "supplier_optimization"
    INVENTORY_OPTIMIZATION = "inventory_optimization"
    SIMULATION_SCENARIO = "simulation_scenario"


class TaskPriority(str, Enum):
    """Task priority levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Individual task status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"