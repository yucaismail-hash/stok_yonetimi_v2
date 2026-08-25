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
from app.auth import get_current_user
from app.database import get_db
from app.schemas.workflow import (
    BusinessWorkflowResultResponse,
    BusinessWorkflowStartRequest,
    BusinessWorkflowStartResponse,
    BusinessWorkflowStatusResponse,
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
