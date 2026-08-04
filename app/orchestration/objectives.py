# app/orchestration/objectives.py
"""
Business Objective Definitions
DOCUMENT 01 - Workflow Principle
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class ObjectiveType(str, Enum):
    """Business objective types."""
    REDUCE_STOCKOUT = "reduce_stockout"
    OPTIMIZE_INVENTORY = "optimize_inventory"
    IMPROVE_SUPPLIER_PERFORMANCE = "improve_supplier_performance"
    FORECAST_DEMAND = "forecast_demand"
    OPTIMIZE_SAFETY_STOCK = "optimize_safety_stock"
    SIMULATE_SCENARIO = "simulate_scenario"
    BACKTEST_MODEL = "backtest_model"


@dataclass
class WorkflowStep:
    """Single step in a workflow."""
    step_type: str  # forecast, safety_stock, simulation, backtest, supplier
    is_functional: bool = True  # True=Functional, False=Enrichment
    depends_on: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    can_skip: bool = False


@dataclass
class BusinessObjective:
    """Business objective definition with workflow steps."""
    objective_type: ObjectiveType
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
# OBJECTIVE DEFINITIONS
# ============================================

OBJECTIVE_REGISTRY: Dict[ObjectiveType, BusinessObjective] = {
    ObjectiveType.FORECAST_DEMAND: BusinessObjective(
        objective_type=ObjectiveType.FORECAST_DEMAND,
        name="Talep Tahmini",
        description="Gelecek dönem talep tahmini yapar",
        steps=[
            WorkflowStep(step_type="forecast", is_functional=True, params={"horizon": 13}),
            WorkflowStep(step_type="backtest", is_functional=False, depends_on=["forecast"], can_skip=True),
        ]
    ),
    
    ObjectiveType.OPTIMIZE_SAFETY_STOCK: BusinessObjective(
        objective_type=ObjectiveType.OPTIMIZE_SAFETY_STOCK,
        name="Emniyet Stoku Optimizasyonu",
        description="Servis seviyesine göre optimal emniyet stoğu hesaplar",
        steps=[
            WorkflowStep(step_type="forecast", is_functional=True, params={"horizon": 13}),
            WorkflowStep(step_type="safety_stock", is_functional=True, depends_on=["forecast"]),
            WorkflowStep(step_type="simulation", is_functional=False, depends_on=["safety_stock"], can_skip=True),
        ]
    ),
    
    ObjectiveType.REDUCE_STOCKOUT: BusinessObjective(
        objective_type=ObjectiveType.REDUCE_STOCKOUT,
        name="Stok Azaltma Risk Yönetimi",
        description="Stok azaltma riskini minimize eder",
        steps=[
            WorkflowStep(step_type="forecast", is_functional=True, params={"horizon": 26}),
            WorkflowStep(step_type="safety_stock", is_functional=True, depends_on=["forecast"]),
            WorkflowStep(step_type="simulation", is_functional=True, depends_on=["safety_stock"]),
            WorkflowStep(step_type="backtest", is_functional=False, depends_on=["simulation"], can_skip=True),
            WorkflowStep(step_type="supplier", is_functional=False, can_skip=True),
        ]
    ),
    
    ObjectiveType.OPTIMIZE_INVENTORY: BusinessObjective(
        objective_type=ObjectiveType.OPTIMIZE_INVENTORY,
        name="Stok Optimizasyonu",
        description="Maliyet ve servis dengesinde optimal stok seviyesi",
        steps=[
            WorkflowStep(step_type="forecast", is_functional=True, params={"horizon": 26}),
            WorkflowStep(step_type="safety_stock", is_functional=True, depends_on=["forecast"]),
            WorkflowStep(step_type="simulation", is_functional=True, depends_on=["safety_stock"]),
            WorkflowStep(step_type="supplier", is_functional=False, can_skip=True),
            WorkflowStep(step_type="backtest", is_functional=False, depends_on=["simulation"], can_skip=True),
        ]
    ),
    
    ObjectiveType.IMPROVE_SUPPLIER_PERFORMANCE: BusinessObjective(
        objective_type=ObjectiveType.IMPROVE_SUPPLIER_PERFORMANCE,
        name="Tedarikçi Performans İyileştirme",
        description="Tedarikçi risk ve performans analizi",
        steps=[
            WorkflowStep(step_type="forecast", is_functional=True, params={"horizon": 13}),
            WorkflowStep(step_type="supplier", is_functional=True, depends_on=["forecast"]),
            WorkflowStep(step_type="safety_stock", is_functional=False, depends_on=["forecast"], can_skip=True),
        ]
    ),
    
    ObjectiveType.SIMULATE_SCENARIO: BusinessObjective(
        objective_type=ObjectiveType.SIMULATE_SCENARIO,
        name="Senaryo Simülasyonu",
        description="Farklı senaryolarda stok davranışını simüle eder",
        steps=[
            WorkflowStep(step_type="forecast", is_functional=True, params={"horizon": 26}),
            WorkflowStep(step_type="simulation", is_functional=True, depends_on=["forecast"]),
            WorkflowStep(step_type="safety_stock", is_functional=False, depends_on=["simulation"], can_skip=True),
        ]
    ),
    
    ObjectiveType.BACKTEST_MODEL: BusinessObjective(
        objective_type=ObjectiveType.BACKTEST_MODEL,
        name="Model Geriye Dönük Test",
        description="Tahmin modellerinin doğruluğunu test eder",
        steps=[
            WorkflowStep(step_type="forecast", is_functional=True, params={"horizon": 13}),
            WorkflowStep(step_type="backtest", is_functional=True, depends_on=["forecast"]),
            WorkflowStep(step_type="simulation", is_functional=False, depends_on=["backtest"], can_skip=True),
        ]
    ),
}


def get_objective(objective_type: ObjectiveType) -> Optional[BusinessObjective]:
    """Get objective by type."""
    return OBJECTIVE_REGISTRY.get(objective_type)


def list_objectives() -> List[Dict[str, Any]]:
    """List all available objectives."""
    return [
        {
            "type": obj.objective_type.value,
            "name": obj.name,
            "description": obj.description,
            "steps": [
                {
                    "step_type": s.step_type,
                    "is_functional": s.is_functional,
                    "depends_on": s.depends_on,
                    "can_skip": s.can_skip,
                }
                for s in obj.steps
            ]
        }
        for obj in OBJECTIVE_REGISTRY.values()
    ]