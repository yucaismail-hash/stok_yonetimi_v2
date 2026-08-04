# app/engine/tests/test_workflow_engine.py
"""
Workflow Engine Tests
DOCUMENT 04 - PART 02
"""

import pytest
from uuid import uuid4

from app.engine.enums import BusinessObjective, TaskType
from app.engine.workflow_engine import WorkflowEngine, WorkflowTemplate
from app.engine.business_objectives import WorkflowStep
from app.engine.workflow_generator import Task


def test_workflow_generation():
    """Test workflow generation from business objective."""
    engine = WorkflowEngine()
    
    workflow = engine.generate_workflow(
        objective_type=BusinessObjective.DEMAND_FORECAST,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    assert workflow.objective_type == BusinessObjective.DEMAND_FORECAST
    assert len(workflow.tasks) > 0
    assert workflow.workflow_id is not None


def test_dependency_resolution():
    """Test dependency resolution."""
    engine = WorkflowEngine()
    
    workflow = engine.generate_workflow(
        objective_type=BusinessObjective.SAFETY_STOCK_OPTIMIZATION,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    resolution = engine.resolve_dependencies(workflow)
    
    # Functional dependencies should be resolved
    assert "forecast" in [t.value for t in resolution.functional_available]
    assert "safety_stock" in [t.value for t in resolution.functional_available]
    
    # Should be executable
    assert resolution.can_execute is True


def test_circular_dependency_detection():
    """Test circular dependency detection."""
    engine = WorkflowEngine()
    
    # Create workflow with circular dependency
    workflow = engine.generate_workflow(
        objective_type=BusinessObjective.DEMAND_FORECAST,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    # Manually create circular dependency
    forecast_task = None
    decision_task = None
    
    for task in workflow.tasks:
        if task.task_type == TaskType.FORECAST:
            forecast_task = task
        if task.task_type == TaskType.DECISION_LEARNING:
            decision_task = task
    
    if forecast_task and decision_task:
        # Add circular dependency: forecast depends on decision_learning
        # This should cause validation to fail
        forecast_task.depends_on.append(TaskType.DECISION_LEARNING)
        
        with pytest.raises(ValueError, match="Circular dependency"):
            engine.validate_workflow(workflow)


def test_execution_graph():
    """Test execution graph generation."""
    engine = WorkflowEngine()
    
    workflow = engine.generate_workflow(
        objective_type=BusinessObjective.INVENTORY_OPTIMIZATION,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    graph = engine.get_execution_graph(workflow)
    
    assert graph["node_count"] == len(workflow.tasks)
    assert graph["is_dag"] is True
    assert len(graph["nodes"]) > 0
    assert "workflow_id" in graph


def test_execution_plan():
    """Test execution plan generation."""
    engine = WorkflowEngine()
    
    workflow = engine.generate_workflow(
        objective_type=BusinessObjective.SUPPLIER_OPTIMIZATION,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
    )
    
    plan = engine.get_execution_plan(workflow)
    
    assert len(plan) == len(workflow.tasks)
    # Forecast should be first
    assert plan[0]["task_type"] == "forecast"
    # Supplier should be after forecast
    supplier_idx = next(i for i, t in enumerate(plan) if t["task_type"] == "supplier")
    forecast_idx = next(i for i, t in enumerate(plan) if t["task_type"] == "forecast")
    assert supplier_idx > forecast_idx


def test_filter_by_available_engines():
    """Test filtering tasks by available engines."""
    engine = WorkflowEngine()
    
    available_engines = {"forecast", "safety_stock"}
    
    workflow = engine.generate_workflow(
        objective_type=BusinessObjective.INVENTORY_OPTIMIZATION,
        dataset_id=str(uuid4()),
        user_id=str(uuid4()),
        company_id=str(uuid4()),
        available_engines=available_engines,
    )
    
    # Functional tasks should be available
    forecast_available = any(
        t.task_type == TaskType.FORECAST and t.status.value != "skipped"
        for t in workflow.tasks
    )
    safety_stock_available = any(
        t.task_type == TaskType.SAFETY_STOCK and t.status.value != "skipped"
        for t in workflow.tasks
    )
    
    assert forecast_available is True
    assert safety_stock_available is True