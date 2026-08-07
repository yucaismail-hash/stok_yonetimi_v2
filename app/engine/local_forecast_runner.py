"""Transitional durable worker for the single standalone Forecast capability."""
from datetime import datetime, timezone

from app.database import SessionLocal
from app.engine.adapters.forecast_adapter import forecast_adapter
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_executor import CapabilityExecutor
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider
from app.engine.enums import TaskStatus
from app.engine.runtime_store import RuntimeStore
from app.analysis.forecast import DemandForecaster


class LocalForecastRunner:
    """Runs one claimed durable Forecast task; no scheduling or queue ownership."""

    def __init__(self, session_factory=SessionLocal, worker_id="local_forecast_runner", lease_seconds=300):
        self._session_factory = session_factory
        self._worker_id = worker_id
        self._lease_seconds = lease_seconds

    def _executor(self, session):
        return CapabilityExecutor(
            lambda capability: DemandForecaster if capability is Capability.DEMAND_FORECAST else None,
            DatasetRuntimeProvider(session), forecast_adapter, lambda invoke, timeout: invoke(),
        )

    async def run(self, execution_id):
        session = self._session_factory()
        try:
            store = RuntimeStore(session)
            execution = store.get_execution_by_id(execution_id)
            if execution is None:
                raise LookupError(f"execution not found: {execution_id}")
            if execution.analysis_type != "forecast":
                raise ValueError("LocalForecastRunner accepts only standalone forecast executions")
            if execution.state == "queued":
                execution = store.transition_execution(execution.execution_id, execution.company_id, "queued", "running", execution.row_version, current_stage="forecast", started_at=datetime.now(timezone.utc))
                session.commit()
            task = store.get_tasks(execution.execution_id, execution.company_id)
            if len(task) != 1 or task[0].capability != Capability.DEMAND_FORECAST.value:
                raise RuntimeError("standalone forecast must contain exactly one demand_forecast task")
            task, attempt = store.claim_task(execution.execution_id, task[0].task_id, execution.company_id, self._worker_id, self._lease_seconds, task[0].row_version)
            session.commit()
            request = CapabilityExecutionRequest(execution.execution_id, execution.workflow_id, task.task_id, Capability.DEMAND_FORECAST, execution.company_id, execution.user_id, execution.dataset_id, task.timeout_seconds or self._lease_seconds, material_codes=(execution.metadata_ or {}).get("material_codes"), params=(execution.metadata_ or {}).get("params", {}), trace_id=execution.trace_id, correlation_id=execution.correlation_id, attempt=attempt.attempt_number)
            result = await self._executor(session).execute(request)
            session.expire_all(); execution = store.get_execution(execution.execution_id, execution.company_id)
            if result.state is TaskStatus.COMPLETED:
                reference = store.complete_task_attempt(execution.execution_id, task.task_id, execution.company_id, task.lease_token, "forecast", result.result, result.result_version, result.contract_version)
                session.flush(); session.refresh(execution)
                store.complete_execution(execution.execution_id, execution.company_id, execution.row_version)
                session.commit()
                return reference
            error = result.errors[0].to_dict()
            failed = store.fail_task_attempt(execution.execution_id, task.task_id, execution.company_id, task.lease_token, error, result.errors[0].retryable)
            session.flush(); session.refresh(execution)
            # This transitional runner has no retry scheduler: terminalize this execution.
            store.fail_execution(execution.execution_id, execution.company_id, execution.row_version, error)
            session.commit()
            return None
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
