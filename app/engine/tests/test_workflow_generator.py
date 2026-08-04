# app/engine/tests/test_workflow_generator.py
"""
Workflow Generator Tests
"""

# pytest app/engine/tests/test_workflow_generator.py -v

import pytest
from uuid import uuid4

from app.engine.enums import BusinessObjective
from app.engine.workflow_generator import WorkflowGenerator


def test_generate_demand_forecast():
    """Test demand forecast workflow generation."""
    generator = WorkflowGenerator()
    
    workflow = generator.generate(
        objective_type=BusinessObjective.DEMAND_FORECAST,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    assert workflow.objective_type == BusinessObjective.DEMAND_FORECAST
    assert len(workflow.tasks) == 3  # forecast, backtest, decision_learning
    assert workflow.tasks[0].task_type.value == "forecast"
    assert workflow.state.value == "created"


def test_generate_safety_stock():
    """Test safety stock workflow generation."""
    generator = WorkflowGenerator()
    
    workflow = generator.generate(
        objective_type=BusinessObjective.SAFETY_STOCK_OPTIMIZATION,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    assert workflow.objective_type == BusinessObjective.SAFETY_STOCK_OPTIMIZATION
    assert len(workflow.tasks) == 4  # forecast, safety_stock, simulation, decision_learning


def test_execution_order():
    """Test execution order generation."""
    generator = WorkflowGenerator()
    
    workflow = generator.generate(
        objective_type=BusinessObjective.INVENTORY_OPTIMIZATION,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    order = generator.get_execution_order(workflow)
    
    # Forecast should be first
    assert order[0].task_type.value == "forecast"
    
    # Safety stock should be after forecast
    safety_stock_idx = next(i for i, t in enumerate(order) if t.task_type.value == "safety_stock")
    forecast_idx = next(i for i, t in enumerate(order) if t.task_type.value == "forecast")
    assert safety_stock_idx > forecast_idx


def test_get_objectives():
    """Test listing objectives."""
    generator = WorkflowGenerator()
    objectives = generator.get_available_objectives()
    
    assert len(objectives) == 5
    objective_types = [o["type"] for o in objectives]
    assert "demand_forecast" in objective_types
    assert "safety_stock_optimization" in objective_types
    assert "supplier_optimization" in objective_types
    assert "inventory_optimization" in objective_types
    assert "simulation_scenario" in objective_types