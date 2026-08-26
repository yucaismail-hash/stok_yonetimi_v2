"""Transitional durable worker for standalone Forecast and Safety Stock capabilities."""
from datetime import datetime, timezone
import logging

from app.database import SessionLocal
from app.engine.adapters.forecast_adapter import forecast_adapter
from app.engine.adapters.safety_stock_adapter import safety_stock_adapter
from app.engine.adapters.simulation_adapter import simulation_adapter
from app.engine.adapters.backtest_adapter import backtest_adapter
from app.engine.adapters.supplier_adapter import supplier_adapter
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_executor import CapabilityExecutor
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider
from app.engine.enums import TaskStatus
from app.engine.runtime_store import RuntimeStore
from app.analysis.forecast import DemandForecaster
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.simulation.monte_carlo import MonteCarloInventorySimulator
from app.analysis.backtest import BacktestEngine
from app.analysis.supplier import SupplierPerformanceAnalyzer


logger = logging.getLogger(__name__)


class LocalForecastRunner:
    """Compatibility name for the small durable Forecast/Safety Stock runner."""

    def __init__(self, session_factory=SessionLocal, worker_id="local_forecast_runner", lease_seconds=300):
        self._session_factory = session_factory
        self._worker_id = worker_id
        self._lease_seconds = lease_seconds

    def _executor(self, session):
        return CapabilityExecutor(
            lambda capability: {Capability.DEMAND_FORECAST: DemandForecaster, Capability.SAFETY_STOCK: ComprehensiveSafetyStockOptimizer, Capability.SIMULATION: MonteCarloInventorySimulator, Capability.BACKTEST:BacktestEngine,Capability.SUPPLIER_ANALYSIS:SupplierPerformanceAnalyzer}.get(capability),
            DatasetRuntimeProvider(session), lambda implementation, prepared, request: {Capability.DEMAND_FORECAST:forecast_adapter,Capability.SAFETY_STOCK:safety_stock_adapter,Capability.SIMULATION:simulation_adapter,Capability.BACKTEST:backtest_adapter,Capability.SUPPLIER_ANALYSIS:supplier_adapter}[request.capability](implementation, prepared, request), lambda invoke, timeout: invoke(),
        )

    async def run(self, execution_id):
        session = self._session_factory()
        try:
            store = RuntimeStore(session)
            execution = store.get_execution_by_id(execution_id)
            if execution is None:
                raise LookupError(f"execution not found: {execution_id}")
            if execution.analysis_type not in ("forecast", "safety_stock", "simulation", "backtest", "supplier"):
                raise ValueError("runner accepts only wired standalone capabilities")
            if execution.state == "queued":
                execution = store.transition_execution(execution.execution_id, execution.company_id, "queued", "running", execution.row_version, current_stage="forecast", started_at=datetime.now(timezone.utc))
                session.commit()
            task = store.get_tasks(execution.execution_id, execution.company_id)
            expected_capability = {'forecast':Capability.DEMAND_FORECAST,'safety_stock':Capability.SAFETY_STOCK,'simulation':Capability.SIMULATION,'backtest':Capability.BACKTEST,'supplier':Capability.SUPPLIER_ANALYSIS}[execution.analysis_type]
            if len(task) != 1 or task[0].capability != expected_capability.value:
                raise RuntimeError("standalone execution must contain exactly one matching capability task")
            task, attempt = store.claim_task(execution.execution_id, task[0].task_id, execution.company_id, self._worker_id, self._lease_seconds, task[0].row_version)
            session.commit()
            request = CapabilityExecutionRequest(execution.execution_id, execution.workflow_id, task.task_id, expected_capability, execution.company_id, execution.user_id, execution.dataset_id, task.timeout_seconds or self._lease_seconds, material_codes=(execution.metadata_ or {}).get("material_codes"), params=(execution.metadata_ or {}).get("params", {}), trace_id=execution.trace_id, correlation_id=execution.correlation_id, attempt=attempt.attempt_number)
            result = await self._executor(session).execute(request)
            session.expire_all(); execution = store.get_execution(execution.execution_id, execution.company_id)
            if result.state is TaskStatus.COMPLETED:
                reference = store.complete_task_attempt(execution.execution_id, task.task_id, execution.company_id, task.lease_token, execution.analysis_type, result.result, result.result_version, result.contract_version)
                session.flush(); session.refresh(execution)
                if expected_capability is Capability.DEMAND_FORECAST:
                    from app.application.forecast_vintage_service import ForecastVintageService
                    session.refresh(reference); ForecastVintageService(session).project(execution, reference, request.params)
                store.complete_execution(execution.execution_id, execution.company_id, execution.row_version)
                session.refresh(reference)
                session.expunge(reference)
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
    async def run_business_task(self, execution_id, company_id, task_id):
        """Phase 3A2B1: execute only the ready Forecast task in a business workflow."""
        session=self._session_factory()
        try:
            store=RuntimeStore(session); execution=store.get_execution(execution_id,company_id); task=[t for t in store.get_tasks(execution_id,company_id) if t.task_id==task_id][0]
            if execution.state=='queued': execution=store.transition_execution(execution_id,company_id,'queued','running',execution.row_version,current_stage='forecast');session.commit()
            task,attempt=store.claim_task(execution_id,task_id,company_id,self._worker_id,self._lease_seconds,task.row_version);session.commit()
            capability={'demand_forecast':Capability.DEMAND_FORECAST,'safety_stock':Capability.SAFETY_STOCK,'supplier':Capability.SUPPLIER_ANALYSIS,'simulation':Capability.SIMULATION,'backtest':Capability.BACKTEST}[task.capability]
            upstream={}
            if capability is Capability.SAFETY_STOCK and any(t.task_id=='supplier' for t in store.get_tasks(execution_id,company_id)):
                from app.engine.capability_dataflow import resolve_business_upstream
                upstream=resolve_business_upstream(store,execution_id,company_id,required=('supplier',))
            if capability is Capability.SIMULATION:
                from app.engine.capability_dataflow import resolve_business_upstream
                required=('forecast','safety_stock','supplier') if any(t.task_id=='supplier' for t in store.get_tasks(execution_id,company_id)) else ('forecast','safety_stock')
                upstream=resolve_business_upstream(store,execution_id,company_id,required=required)
            if capability is Capability.BACKTEST:
                upstream={'safety_stock':store.get_validated_upstream_result(execution_id,'safety_stock',company_id)}
            params=(execution.metadata_ or {}).get('request_metadata',{}).get('params',{})
            if capability is Capability.BACKTEST: params={**params,'mode':'VALIDATE_SELECTED'}
            request=CapabilityExecutionRequest(execution_id,execution.workflow_id,task_id,capability,company_id,execution.user_id,execution.dataset_id,task.timeout_seconds or 300,params=params,upstream_results=upstream,attempt=attempt.attempt_number)
            result=await self._executor(session).execute(request)
            if result.state is not TaskStatus.COMPLETED:
                error=result.errors[0].to_dict()
                failed=store.fail_task_attempt(execution_id,task_id,company_id,task.lease_token,error,result.errors[0].retryable)
                session.flush(); session.refresh(execution)
                if failed.state == 'failed':
                    store.fail_execution(execution_id,company_id,execution.row_version,error,current_stage=failed.task_id)
                session.commit(); return None
            result_type={Capability.DEMAND_FORECAST:'forecast',Capability.SAFETY_STOCK:'safety_stock',Capability.SUPPLIER_ANALYSIS:'supplier',Capability.SIMULATION:'simulation',Capability.BACKTEST:'backtest'}[capability]
            ref=store.complete_task_attempt(execution_id,task_id,company_id,task.lease_token,result_type,result.result);session.flush();session.refresh(execution)
            if capability is Capability.DEMAND_FORECAST:
                from app.application.forecast_vintage_service import ForecastVintageService
                session.refresh(ref); ForecastVintageService(session).project(execution,ref,params)
            terminal_analytics = False
            if all(t.state=='completed' for t in store.get_tasks(execution_id,company_id) if t.required):
                store.complete_execution(execution_id,company_id,execution.row_version)
                store.aggregate_business_workflow(execution_id,company_id)
                terminal_analytics = True
            session.refresh(ref);session.expunge(ref)
            session.commit()
            if terminal_analytics:
                # Advisory Decision work begins only after the analytical terminal
                # transaction has committed. It must never change that outcome.
                try:
                    from app.application.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalizationService
                    BusinessWorkflowDecisionFinalizationService().finalize(company_id, execution_id)
                except Exception:
                    # If lifecycle persistence itself is temporarily unavailable, the
                    # completed workflow remains authoritative and recovery can retry.
                    logger.exception("post-analytics Decision finalization invocation failed", extra={"execution_id": str(execution_id), "company_id": str(company_id)})
            return ref
        finally: session.close()
