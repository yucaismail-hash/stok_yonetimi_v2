"""Real PostgreSQL cross-process recovery probe for the Business Workflow."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.analysis.forecast import DemandForecaster
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.engine.runtime_store import RuntimeStore
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


def fresh(execution_id):
    """Build a new ORM/scheduler graph; execution_id is the only retained runtime value."""
    session = SessionLocal()
    execution = RuntimeStore(session).get_execution_by_id(execution_id)
    assert execution is not None
    return session, execution.company_id


def readiness_by_task(session, execution_id, company_id):
    return {row["task_id"]: row for row in BusinessWorkflowScheduler(session).readiness(execution_id, company_id)}


async def main():
    session = SessionLocal(); company = user = None; company_id = user_id = None
    probe = "phase3a3_" + str(uuid7()).replace("-", "")
    started = perf_counter()
    try:
        company = Company(id=uuid7(), name=probe, tax_id=probe); company_id = company.id
        user = User(id=uuid7(), company_id=company_id, email=probe + "@example.invalid", hashed_password="probe"); user_id = user.id
        session.add_all((company, user)); session.flush()
        history_a = [3, 5, 2, 6, 4, 7, 3, 8, 4, 9, 5, 10, 6, 11, 7, 12, 8, 13]
        history_b = [0, 8, 0, 11, 0, 7, 0, 12, 0, 9, 0, 13, 0, 10, 0, 14, 0, 15]
        payload = {"items": [
            {"sku_code": "RECOVERY-A", "demand_history": history_a, "lead_time_days": 14, "initial_stock": 80, "eoq": 25},
            {"sku_code": "RECOVERY-B", "demand_history": history_b, "lead_time_days": 21, "initial_stock": 50, "eoq": 20},
        ]}
        dataset = Dataset(id=uuid7(), company_id=company_id, user_id=user_id, uploaded_by=user_id, dataset_hash=hashlib.sha256(json.dumps(payload).encode()).hexdigest(), source_type=probe, encrypted_data=EncryptionService(session).encrypt_dataset(user_id, payload), is_active=True)
        session.add(dataset); session.commit()
        execution_id = BusinessWorkflowAcceptanceService().accept(company_id, user_id, dataset.id, request_metadata={"params": {"n_simulations": 8, "weeks": 3, "test_window": 12}})
        session.close(); session = None

        # Point A: Forecast, then lose every runtime object except execution_id.
        session, recovered_company_id = fresh(execution_id)
        assert (await BusinessWorkflowScheduler(session).run_next_ready(execution_id, recovered_company_id)).result_type == "forecast"
        session.close(); session, recovered_company_id = fresh(execution_id)
        execution = RuntimeStore(session).get_execution(execution_id, recovered_company_id); ready = readiness_by_task(session, execution_id, recovered_company_id)
        assert float(execution.progress) == 25 and ready["safety_stock"]["ready"] and not ready["simulation"]["ready"] and not ready["backtest"]["ready"]

        # Business tasks use max_attempts=1. An expired claim therefore cannot be reclaimed without a
        # future retry-policy change; keep this recovery proof within the current durable contract.
        assert (await BusinessWorkflowScheduler(session).run_next_ready(execution_id, recovered_company_id)).result_type == "safety_stock"
        session.close()

        # Point B: reconstruct persisted results, then deterministically run Simulation.
        session, recovered_company_id = fresh(execution_id); execution = RuntimeStore(session).get_execution(execution_id, recovered_company_id); ready = readiness_by_task(session, execution_id, recovered_company_id)
        assert float(execution.progress) == 50 and ready["simulation"]["ready"] and ready["backtest"]["ready"]
        calls = {"forecast": 0, "safety_stock": 0}; original_forecast = DemandForecaster.forecast; original_safety = ComprehensiveSafetyStockOptimizer.calculate_all_methods
        def counted_forecast(self, *args, **kwargs): calls["forecast"] += 1; return original_forecast(self, *args, **kwargs)
        def counted_safety(self, *args, **kwargs): calls["safety_stock"] += 1; return original_safety(self, *args, **kwargs)
        DemandForecaster.forecast = counted_forecast; ComprehensiveSafetyStockOptimizer.calculate_all_methods = counted_safety
        try:
            assert (await BusinessWorkflowScheduler(session).run_next_ready(execution_id, recovered_company_id)).result_type == "simulation"
        finally:
            DemandForecaster.forecast = original_forecast; ComprehensiveSafetyStockOptimizer.calculate_all_methods = original_safety
        assert calls == {"forecast": 0, "safety_stock": 0}; session.close()

        # Point C: Backtest is now the sole ready task and reloads Safety Stock provenance from PostgreSQL.
        session, recovered_company_id = fresh(execution_id); execution = RuntimeStore(session).get_execution(execution_id, recovered_company_id); ready = readiness_by_task(session, execution_id, recovered_company_id)
        assert float(execution.progress) == 75 and [name for name, row in ready.items() if row["ready"]] == ["backtest"]
        assert (await BusinessWorkflowScheduler(session).run_next_ready(execution_id, recovered_company_id)).result_type == "backtest"
        session.close()

        # Completed recovery / re-entry protection, result uniqueness, and stable provenance.
        session, recovered_company_id = fresh(execution_id); store = RuntimeStore(session); execution = store.get_execution(execution_id, recovered_company_id)
        tasks = {task.task_id: task for task in store.get_tasks(execution_id, recovered_company_id)}; refs = store.get_execution_result_references(execution_id, recovered_company_id); by_type = {ref.result_type: ref for ref in refs}
        before_attempts = session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id).count()
        assert execution.state == "completed" and float(execution.progress) == 100 and set(tasks) == {"forecast", "safety_stock", "simulation", "backtest"} and all(task.state == "completed" for task in tasks.values())
        assert session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id, state="completed").count() == 4
        assert {ref.result_type for ref in refs} == {"forecast", "safety_stock", "simulation", "backtest"} and all(ref.validation_status == "validated" for ref in refs)
        assert {kind: sum(ref.result_type == kind for ref in refs) for kind in by_type} == {"forecast": 1, "safety_stock": 1, "simulation": 1, "backtest": 1}
        assert not any(row["ready"] for row in readiness_by_task(session, execution_id, recovered_company_id).values())
        assert await BusinessWorkflowScheduler(session).run_next_ready(execution_id, recovered_company_id) is None
        assert session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id).count() == before_attempts
        forecast_id, safety_id = str(by_type["forecast"].id), str(by_type["safety_stock"].id)
        for item in by_type["simulation"].inline_result["items"]:
            assert item["forecast_source"] == "upstream" and item["safety_stock_source"] == "upstream"
            assert item["provenance"]["forecast"]["result_reference_id"] == forecast_id and item["provenance"]["safety_stock"]["result_reference_id"] == safety_id
        for item in by_type["backtest"].inline_result["items"]:
            assert item["backtest_mode"] == "VALIDATE_SELECTED" and item["strategies_tested"] == ["hybrid"] and item["provenance"]["result_reference_id"] == safety_id
        durations = {task_id: [float(row.duration_ms) for row in session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id, runtime_task_id=task.id).all() if row.duration_ms is not None] for task_id, task in tasks.items()}
        print("PHASE3A3 PASS", json.dumps({"execution_id": str(execution_id), "recoveries": 4, "progress": [25, 50, 75, 100], "attempts_per_task": {name: task.current_attempt for name, task in tasks.items()}, "completed_attempts": 4, "result_references": 4, "simulation_recomputation": calls, "expired_lease_recovery": "DOCUMENTED_GAP:max_attempts=1", "durations_ms": durations, "total_workflow_ms": round((perf_counter() - started) * 1000, 3)}), flush=True)
    finally:
        if session is not None:
            session.rollback()
            if company_id is not None:
                ids = [value[0] for value in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id).all()]
                if ids:
                    for model in (RuntimeResultReference, RuntimeTaskAttempt, RuntimeTask): session.query(model).filter(model.execution_id.in_(ids)).delete(synchronize_session=False)
                    session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
                session.query(Dataset).filter_by(source_type=probe).delete(synchronize_session=False)
                session.query(CompanyEncryptionKey).filter_by(user_id=user_id).delete(synchronize_session=False)
                session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
                session.query(Company).filter_by(id=company_id).delete(synchronize_session=False)
                session.commit()
            session.close()


if __name__ == "__main__":
    asyncio.run(main())
