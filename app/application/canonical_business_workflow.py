"""Application boundary for the canonical first-user Business Workflow API."""

from uuid import UUID

from app.application.business_workflow_acceptance import (
    BUSINESS_WORKFLOW_TYPE,
    BusinessWorkflowAcceptanceService,
    BusinessWorkflowNotReadyError,
)
from app.application.canonical_excel_ingestion import CanonicalExcelIngestionService
from app.engine.runtime_store import RuntimeStore


class WorkflowDatasetUnavailableError(RuntimeError):
    pass


class WorkflowReadinessBlockedError(WorkflowDatasetUnavailableError):
    def __init__(self, readiness):
        self.readiness = readiness
        super().__init__("BUSINESS_WORKFLOW_NOT_READY")


class WorkflowNotFoundError(LookupError):
    pass


class WorkflowResultNotReadyError(RuntimeError):
    pass


class WorkflowResultUnavailableError(LookupError):
    pass


class CanonicalBusinessWorkflowService:
    def __init__(self, acceptance_service=None):
        self._acceptance = acceptance_service or BusinessWorkflowAcceptanceService()

    def start(self, session, company_id: UUID, user_id: UUID):
        current = CanonicalExcelIngestionService().get_current_accepted(session, company_id)
        if current is None:
            raise WorkflowDatasetUnavailableError("No workflow-ready dataset is available")

        dataset_id = UUID(current["dataset_id"])
        try:
            accepted = self._acceptance.accept_or_resolve(
                company_id=company_id,
                user_id=user_id,
                dataset_id=dataset_id,
                request_metadata={"source": "canonical_business_workflow_api"},
            )
        except BusinessWorkflowNotReadyError as exc:
            raise WorkflowReadinessBlockedError(exc.readiness) from exc
        execution = RuntimeStore(session).get_execution(accepted.execution_id, company_id)
        if execution is None:
            raise RuntimeError("Accepted workflow could not be read back")
        return execution, accepted.status == "ALREADY_RUNNING"

    @staticmethod
    def get_status(session, company_id: UUID, execution_id: UUID):
        execution = RuntimeStore(session).get_execution(execution_id, company_id)
        if execution is None or execution.analysis_type != BUSINESS_WORKFLOW_TYPE:
            raise WorkflowNotFoundError("Workflow execution was not found")
        return execution

    @staticmethod
    def get_result(session, company_id: UUID, execution_id: UUID):
        store = RuntimeStore(session)
        execution = store.get_execution(execution_id, company_id)
        if execution is None or execution.analysis_type != BUSINESS_WORKFLOW_TYPE:
            raise WorkflowNotFoundError("Workflow execution was not found")
        if execution.state != "completed":
            raise WorkflowResultNotReadyError("Workflow result is not available before completion")
        reference = store.get_execution_aggregate_result(execution_id, company_id)
        if reference is None or not isinstance(reference.inline_result, dict):
            raise WorkflowResultUnavailableError("Completed workflow result was not found")
        result = dict(reference.inline_result)
        result.pop("company_id", None)
        return execution, result
