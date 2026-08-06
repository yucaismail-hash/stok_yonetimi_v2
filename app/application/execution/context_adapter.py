"""Application-to-engine conversion for planned workflow dispatch requests."""

from copy import deepcopy

from app.engine.contracts import WorkflowDispatchRequest
from app.engine.enums import ExecutionState
from app.engine.execution_context import ExecutionContext
from app.engine.workflow_generator import Workflow


class ExecutionContextAdapter:
    """Build a canonical mutable engine context from an accepted dispatch request."""

    @staticmethod
    def from_dispatch_request(
        request: WorkflowDispatchRequest,
        workflow: Workflow,
    ) -> ExecutionContext:
        """Create an engine context after a workflow has been planned and validated."""
        if not isinstance(request, WorkflowDispatchRequest):
            raise TypeError("request must be a WorkflowDispatchRequest")
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow must be a Workflow")
        if not isinstance(workflow.workflow_id, str) or not workflow.workflow_id.strip():
            raise ValueError("workflow.workflow_id must be non-empty")

        has_objective = isinstance(request.objective_type, str) and bool(request.objective_type.strip())
        has_analysis = isinstance(request.analysis_type, str) and bool(request.analysis_type.strip())
        if has_objective == has_analysis:
            raise ValueError("request must contain exactly one non-empty intent")

        context = ExecutionContext(
            workflow_id=workflow.workflow_id,
            workflow=workflow,
            execution_id=request.execution_id,
            company_id=request.company_id,
            user_id=request.user_id,
            dataset_id=request.dataset_id,
            objective_type=request.objective_type,
            analysis_type=request.analysis_type,
            material_codes=deepcopy(request.material_codes),
            params=deepcopy(request.params),
            request_id=request.request_id,
            trace_id=request.trace_id,
            correlation_id=request.correlation_id,
            contract_version=request.contract_version,
            state=ExecutionState.CREATED,
            current_stage="planning",
            progress=0.0,
            queued_at=None,
        )
        if context.execution_id != request.execution_id:
            raise RuntimeError("execution_id preservation failed")
        if context.state is not ExecutionState.CREATED or context.current_stage != "planning":
            raise RuntimeError("adapter initialized an invalid runtime state or stage")
        return context
