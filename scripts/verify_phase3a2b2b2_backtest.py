"""PostgreSQL acceptance probe for the four-task Business Workflow."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path

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


async def main():
    session = SessionLocal(); company = user = dataset = None; company_id = user_id = None; probe = "phase3a2b2b2_" + str(uuid7()).replace("-", "")
    try:
        company = Company(id=uuid7(), name=probe, tax_id=probe); company_id = company.id
        user = User(id=uuid7(), company_id=company.id, email=probe + "@example.invalid", hashed_password="probe"); user_id = user.id
        session.add_all((company, user)); session.flush()
        history = [3, 5, 2, 6, 4, 7, 3, 8, 4, 9, 5, 10, 6, 11, 7, 12, 8, 13]
        payload = {"items": [{"sku_code": "PROBE-A", "demand_history": history, "lead_time_days": 14, "initial_stock": 80, "eoq": 25}]}
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id, dataset_hash=hashlib.sha256(json.dumps(payload).encode()).hexdigest(), source_type=probe, encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True)
        session.add(dataset); session.commit()
        execution_id = BusinessWorkflowAcceptanceService().accept(company.id, user.id, dataset.id, request_metadata={"params": {"n_simulations": 8, "weeks": 3, "test_window": 12}})

        progress = []
        for expected_task, expected_progress in (("forecast", 25), ("safety_stock", 50)):
            reference = await BusinessWorkflowScheduler(session).run_next_ready(execution_id, company.id)
            assert reference.result_type == ("forecast" if expected_task == "forecast" else expected_task)
            session.expire_all(); execution = RuntimeStore(session).get_execution(execution_id, company.id)
            assert float(execution.progress) == expected_progress; progress.append(int(execution.progress))

        calls = {"forecast": 0, "safety": 0}
        original_forecast = DemandForecaster.forecast
        original_safety = ComprehensiveSafetyStockOptimizer.calculate_all_methods
        def counted_forecast(self, *args, **kwargs): calls["forecast"] += 1; return original_forecast(self, *args, **kwargs)
        def counted_safety(self, *args, **kwargs): calls["safety"] += 1; return original_safety(self, *args, **kwargs)
        DemandForecaster.forecast = counted_forecast; ComprehensiveSafetyStockOptimizer.calculate_all_methods = counted_safety
        try:
            simulation_reference = await BusinessWorkflowScheduler(session).run_next_ready(execution_id, company.id)
        finally:
            DemandForecaster.forecast = original_forecast; ComprehensiveSafetyStockOptimizer.calculate_all_methods = original_safety
        assert simulation_reference.result_type == "simulation" and calls == {"forecast": 0, "safety": 0}
        session.expire_all(); execution = RuntimeStore(session).get_execution(execution_id, company.id)
        assert float(execution.progress) == 75; progress.append(75)

        backtest_reference = await BusinessWorkflowScheduler(session).run_next_ready(execution_id, company.id)
        assert backtest_reference.result_type == "backtest"
        session.expire_all(); execution = RuntimeStore(session).get_execution(execution_id, company.id)
        assert execution.state == "completed" and float(execution.progress) == 100; progress.append(100)

        # Discard the original object graph, then independently reconstruct from execution_id.
        session.close(); session = SessionLocal(); store = RuntimeStore(session)
        execution = store.get_execution(execution_id, company_id); tasks = {task.task_id: task for task in store.get_tasks(execution_id, company_id)}
        refs = store.get_execution_result_references(execution_id, company_id); by_type = {ref.result_type: ref for ref in refs}
        assert execution.state == "completed" and float(execution.progress) == 100
        assert set(tasks) == {"forecast", "safety_stock", "simulation", "backtest"} and all(task.state == "completed" for task in tasks.values())
        assert session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id, state="completed").count() == 4
        assert set(by_type) == {"forecast", "safety_stock", "simulation", "backtest"} and all(ref.validation_status == "validated" for ref in refs)
        assert not any(row["ready"] for row in BusinessWorkflowScheduler(session).readiness(execution_id, company_id))
        simulation = by_type["simulation"].inline_result["items"][0]
        backtest = by_type["backtest"].inline_result["items"][0]
        safety_id = str(by_type["safety_stock"].id); forecast_id = str(by_type["forecast"].id)
        assert simulation["forecast_source"] == "upstream" and simulation["safety_stock_source"] == "upstream"
        assert simulation["provenance"]["forecast"]["result_reference_id"] == forecast_id and simulation["provenance"]["safety_stock"]["result_reference_id"] == safety_id
        assert backtest["backtest_mode"] == "VALIDATE_SELECTED" and backtest["strategies_tested"] == ["hybrid"] and backtest["validated_strategy"] == "hybrid"
        assert backtest["provenance"]["result_reference_id"] == safety_id
        print("PHASE3A2B2B2 PASS", json.dumps({"execution_id": str(execution_id), "progress": progress, "attempts": 4, "validated_results": 4, "simulation_recomputation": calls, "backtest_strategy": backtest["validated_strategy"]}), flush=True)
    finally:
        session.rollback()
        if company is not None:
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


if __name__ == "__main__": asyncio.run(main())
