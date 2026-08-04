# app/engine/business_objectives.py
"""
Business Objective Definitions
DOCUMENT 04 - Section 6 & 7
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.engine.enums import BusinessObjective, TaskType, TaskPriority


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    task_type: TaskType
    is_functional: bool = True  # True=Functional, False=Enrichment
    depends_on: List[TaskType] = field(default_factory=list)
    can_skip: bool = False
    priority: TaskPriority = TaskPriority.MEDIUM
    retry_count: int = 3
    timeout_seconds: int = 300


@dataclass
class BusinessObjectiveDefinition:
    """Business objective definition with workflow steps."""
    
    objective_type: BusinessObjective
    name: str
    description: str
    steps: List[WorkflowStep]
    requires_dataset: bool = True
    requires_approval: bool = True
    
    def get_functional_steps(self) -> List[WorkflowStep]:
        """Get functional dependencies only."""
        return [s for s in self.steps if s.is_functional]
    
    def get_enrichment_steps(self) -> List[WorkflowStep]:
        """Get enrichment dependencies only."""
        return [s for s in self.steps if not s.is_functional]


# ============================================
# OBJECTIVE REGISTRY
# ============================================

OBJECTIVE_REGISTRY: Dict[BusinessObjective, BusinessObjectiveDefinition] = {
    
    BusinessObjective.DEMAND_FORECAST: BusinessObjectiveDefinition(
        objective_type=BusinessObjective.DEMAND_FORECAST,
        name="Talep Tahmini",
        description="Gelecek dönem talep tahmini yapar",
        steps=[
            WorkflowStep(
                task_type=TaskType.FORECAST,
                is_functional=True,
                depends_on=[],
                priority=TaskPriority.HIGH,
                timeout_seconds=600,
            ),
            WorkflowStep(
                task_type=TaskType.BACKTEST,
                is_functional=False,
                depends_on=[TaskType.FORECAST],
                can_skip=True,
                priority=TaskPriority.MEDIUM,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.DECISION_LEARNING,
                is_functional=False,
                depends_on=[TaskType.FORECAST],
                can_skip=True,
                priority=TaskPriority.LOW,
                timeout_seconds=180,
            ),
        ]
    ),
    
    BusinessObjective.SAFETY_STOCK_OPTIMIZATION: BusinessObjectiveDefinition(
        objective_type=BusinessObjective.SAFETY_STOCK_OPTIMIZATION,
        name="Emniyet Stoku Optimizasyonu",
        description="Servis seviyesine göre optimal emniyet stoğu hesaplar",
        steps=[
            WorkflowStep(
                task_type=TaskType.FORECAST,
                is_functional=True,
                depends_on=[],
                priority=TaskPriority.HIGH,
                timeout_seconds=600,
            ),
            WorkflowStep(
                task_type=TaskType.SAFETY_STOCK,
                is_functional=True,
                depends_on=[TaskType.FORECAST],
                priority=TaskPriority.HIGH,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.SIMULATION,
                is_functional=False,
                depends_on=[TaskType.SAFETY_STOCK],
                can_skip=True,
                priority=TaskPriority.MEDIUM,
                timeout_seconds=900,
            ),
            WorkflowStep(
                task_type=TaskType.DECISION_LEARNING,
                is_functional=False,
                depends_on=[TaskType.SAFETY_STOCK],
                can_skip=True,
                priority=TaskPriority.LOW,
                timeout_seconds=180,
            ),
        ]
    ),
    
    BusinessObjective.SUPPLIER_OPTIMIZATION: BusinessObjectiveDefinition(
        objective_type=BusinessObjective.SUPPLIER_OPTIMIZATION,
        name="Tedarikçi Optimizasyonu",
        description="Tedarikçi risk ve performans analizi",
        steps=[
            WorkflowStep(
                task_type=TaskType.FORECAST,
                is_functional=True,
                depends_on=[],
                priority=TaskPriority.HIGH,
                timeout_seconds=600,
            ),
            WorkflowStep(
                task_type=TaskType.SUPPLIER,
                is_functional=True,
                depends_on=[TaskType.FORECAST],
                priority=TaskPriority.HIGH,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.SAFETY_STOCK,
                is_functional=False,
                depends_on=[TaskType.FORECAST],
                can_skip=True,
                priority=TaskPriority.MEDIUM,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.DECISION_LEARNING,
                is_functional=False,
                depends_on=[TaskType.SUPPLIER],
                can_skip=True,
                priority=TaskPriority.LOW,
                timeout_seconds=180,
            ),
        ]
    ),
    
    BusinessObjective.INVENTORY_OPTIMIZATION: BusinessObjectiveDefinition(
        objective_type=BusinessObjective.INVENTORY_OPTIMIZATION,
        name="Stok Optimizasyonu",
        description="Maliyet ve servis dengesinde optimal stok seviyesi",
        steps=[
            WorkflowStep(
                task_type=TaskType.FORECAST,
                is_functional=True,
                depends_on=[],
                priority=TaskPriority.HIGH,
                timeout_seconds=600,
            ),
            WorkflowStep(
                task_type=TaskType.SAFETY_STOCK,
                is_functional=True,
                depends_on=[TaskType.FORECAST],
                priority=TaskPriority.HIGH,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.SIMULATION,
                is_functional=True,
                depends_on=[TaskType.SAFETY_STOCK],
                priority=TaskPriority.MEDIUM,
                timeout_seconds=900,
            ),
            WorkflowStep(
                task_type=TaskType.SUPPLIER,
                is_functional=False,
                depends_on=[TaskType.FORECAST],
                can_skip=True,
                priority=TaskPriority.MEDIUM,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.BACKTEST,
                is_functional=False,
                depends_on=[TaskType.SIMULATION],
                can_skip=True,
                priority=TaskPriority.LOW,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.DECISION_LEARNING,
                is_functional=False,
                depends_on=[TaskType.SIMULATION],
                can_skip=True,
                priority=TaskPriority.LOW,
                timeout_seconds=180,
            ),
        ]
    ),
    
    BusinessObjective.SIMULATION_SCENARIO: BusinessObjectiveDefinition(
        objective_type=BusinessObjective.SIMULATION_SCENARIO,
        name="Senaryo Simülasyonu",
        description="Farklı senaryolarda stok davranışını simüle eder",
        steps=[
            WorkflowStep(
                task_type=TaskType.FORECAST,
                is_functional=True,
                depends_on=[],
                priority=TaskPriority.HIGH,
                timeout_seconds=600,
            ),
            WorkflowStep(
                task_type=TaskType.SIMULATION,
                is_functional=True,
                depends_on=[TaskType.FORECAST],
                priority=TaskPriority.HIGH,
                timeout_seconds=900,
            ),
            WorkflowStep(
                task_type=TaskType.SAFETY_STOCK,
                is_functional=False,
                depends_on=[TaskType.SIMULATION],
                can_skip=True,
                priority=TaskPriority.MEDIUM,
                timeout_seconds=300,
            ),
            WorkflowStep(
                task_type=TaskType.DECISION_LEARNING,
                is_functional=False,
                depends_on=[TaskType.SIMULATION],
                can_skip=True,
                priority=TaskPriority.LOW,
                timeout_seconds=180,
            ),
        ]
    ),
}


def get_objective(objective_type: BusinessObjective) -> Optional[BusinessObjectiveDefinition]:
    """Get objective definition by type."""
    return OBJECTIVE_REGISTRY.get(objective_type)


def list_objectives() -> List[Dict[str, Any]]:
    """List all available business objectives."""
    return [
        {
            "type": obj.objective_type.value,
            "name": obj.name,
            "description": obj.description,
            "steps": [
                {
                    "task_type": s.task_type.value,
                    "is_functional": s.is_functional,
                    "depends_on": [t.value for t in s.depends_on],
                    "can_skip": s.can_skip,
                    "priority": s.priority.value,
                    "timeout_seconds": s.timeout_seconds,
                }
                for s in obj.steps
            ]
        }
        for obj in OBJECTIVE_REGISTRY.values()
    ]