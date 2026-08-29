"""Canonical authenticated Business Workflow start/status/result endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.application.canonical_business_workflow import (
    CanonicalBusinessWorkflowService,
    WorkflowDatasetUnavailableError,
    WorkflowNotFoundError,
    WorkflowResultNotReadyError,
    WorkflowResultUnavailableError,
)
from app.application.business_workflow_presentation import (
    BusinessWorkflowPresentationIntegrityError,
    BusinessWorkflowPresentationNotFoundError,
    BusinessWorkflowPresentationService,
)
from app.application.decision_feedback import DecisionFeedbackService
from app.auth import get_current_user
from app.database import get_db
from app.schemas.workflow import (
    BusinessWorkflowResultResponse,
    BusinessWorkflowStartRequest,
    BusinessWorkflowStartResponse,
    BusinessWorkflowStatusResponse,
)
from app.schemas.business_workflow_presentation import (
    BusinessWorkflowDecisionPresentationResponse,
)
from app.schemas.decision_feedback import DecisionFeedbackRequest, DecisionFeedbackResponse
from app.engine.runtime_store import RuntimeStore
from app.models.business_workflow_decision_snapshot_reference import (
    BusinessWorkflowDecisionSnapshotReference,
)

router = APIRouter(tags=["Business Workflow"])


@router.post(
    "/workflows/business",
    response_model=BusinessWorkflowStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_business_workflow(
    _request: BusinessWorkflowStartRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        execution, duplicate = CanonicalBusinessWorkflowService().start(
            db, current_user.company_id, current_user.id,
        )
    except WorkflowDatasetUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Workflow could not be queued") from exc

    if duplicate:
        response.status_code = status.HTTP_200_OK
    return BusinessWorkflowStartResponse(
        execution_id=execution.execution_id,
        status=execution.state,
        created_at=execution.created_at,
        workflow_type="business_workflow",
        dataset_id=execution.dataset_id,
        duplicate=duplicate,
    )


@router.get(
    "/executions/{execution_id}",
    response_model=BusinessWorkflowStatusResponse,
)
def get_business_workflow_status(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        execution = CanonicalBusinessWorkflowService.get_status(
            db, current_user.company_id, execution_id,
        )
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    failure = execution.terminal_error
    if isinstance(failure, dict):
        failure = failure.get("code")
    elif failure:
        failure = "WORKFLOW_EXECUTION_FAILED"
    return BusinessWorkflowStatusResponse(
        execution_id=execution.execution_id,
        status=execution.state,
        progress=float(execution.progress),
        current_stage=execution.current_stage,
        created_at=execution.created_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        failed_at=execution.completed_at if execution.state == "failed" else None,
        failure_summary=str(failure) if failure else None,
        dataset_id=execution.dataset_id,
        workflow_type="business_workflow",
        workflow_id=execution.workflow_id,
    )


@router.get(
    "/executions/{execution_id}/result",
    response_model=BusinessWorkflowResultResponse,
)
def get_business_workflow_result(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        execution, result = CanonicalBusinessWorkflowService.get_result(
            db, current_user.company_id, execution_id,
        )
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkflowResultNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WorkflowResultUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return BusinessWorkflowResultResponse(
        execution_id=execution.execution_id,
        workflow_type="business_workflow",
        dataset_id=execution.dataset_id,
        completed_at=execution.completed_at,
        result=result,
    )


@router.get(
    "/executions/{execution_id}/decision",
    response_model=BusinessWorkflowDecisionPresentationResponse,
)
def get_business_workflow_decision_presentation(
    execution_id: UUID,
    current_user=Depends(get_current_user),
):
    """Return only persisted, immutable Decision presentation evidence."""
    try:
        return BusinessWorkflowPresentationService().get(
            current_user.company_id, execution_id,
        )
    except BusinessWorkflowPresentationNotFoundError as exc:
        # Missing and foreign executions intentionally remain indistinguishable.
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BusinessWorkflowPresentationIntegrityError as exc:
        # Do not leak broken provenance details through a public presentation read.
        raise HTTPException(
            status_code=500,
            detail="Workflow Decision presentation is unavailable",
        ) from exc


@router.post(
    "/executions/{execution_id}/decisions/{snapshot_id}/feedback",
    response_model=DecisionFeedbackResponse,
    responses={
        400: {"description": "Feedback semantic validation failed"},
        401: {"description": "Authentication is required"},
        404: {"description": "Business Workflow execution or Decision is unavailable"},
    },
)
def record_business_workflow_decision_feedback(
    execution_id: UUID,
    snapshot_id: UUID,
    request: DecisionFeedbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Append user feedback only for an immutable Snapshot owned by this execution."""
    execution = RuntimeStore(db).get_execution(execution_id, current_user.company_id)
    if execution is None or execution.analysis_type != "business_workflow":
        raise HTTPException(status_code=404, detail="Business Workflow execution was not found")

    association = db.query(BusinessWorkflowDecisionSnapshotReference.id).filter_by(
        company_id=current_user.company_id,
        execution_id=execution_id,
        decision_snapshot_id=snapshot_id,
    ).one_or_none()
    if association is None:
        raise HTTPException(status_code=404, detail="Workflow Decision was not found")

    try:
        result = DecisionFeedbackService().record(
            current_user.company_id,
            current_user.id,
            snapshot_id,
            request.feedback_type,
            candidate_ordinal=request.candidate_ordinal,
            candidate_type=request.candidate_type,
            comment=request.comment,
            source_metadata=request.source_metadata,
            supersedes_feedback_id=request.supersedes_feedback_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DecisionFeedbackResponse(status=result.status, feedback_id=result.feedback_id)
