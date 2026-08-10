"""Real PostgreSQL verification of Business Workflow result aggregation."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.analysis.backtest import BacktestEngine
from app.analysis.forecast import DemandForecaster
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.business_workflow_aggregation import BusinessWorkflowAggregationService
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.engine.runtime_store import RuntimeStore, RuntimeStoreAggregationError
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.simulation.monte_carlo import MonteCarloInventorySimulator


def create_fixture(name, payload):
    probe = "phase3a5_" + name + "_" + str(uuid7()).replace("-", ""); session = SessionLocal()
    try:
        company = Company(id=uuid7(), name=probe, tax_id=probe); user = User(id=uuid7(), company_id=company.id, email=probe + "@example.invalid", hashed_password="probe")
        session.add_all((company, user)); session.flush()
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id, dataset_hash=hashlib.sha256((probe + json.dumps(payload)).encode()).hexdigest(), source_type=probe, encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True)
        session.add(dataset); session.commit(); execution_id = BusinessWorkflowAcceptanceService().accept(company.id, user.id, dataset.id, request_metadata={"params": {"n_simulations": 6, "weeks": 3, "test_window": 12}})
        return probe, company.id, user.id, execution_id
    except Exception:
        session.rollback(); raise
    finally: session.close()


def cleanup(probe, company_id, user_id):
    session = SessionLocal()
    try:
        ids = [value[0] for value in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id).all()]
        if ids:
            for model in (RuntimeResultReference, RuntimeTaskAttempt, RuntimeTask): session.query(model).filter(model.execution_id.in_(ids)).delete(synchronize_session=False)
            session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
        session.query(Dataset).filter_by(source_type=probe).delete(synchronize_session=False)
        session.query(CompanyEncryptionKey).filter_by(user_id=user_id).delete(synchronize_session=False)
        session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
        session.query(Company).filter_by(id=company_id).delete(synchronize_session=False); session.commit()
    finally: session.close()


async def run_steps(execution_id, count):
    for _ in range(count):
        session = SessionLocal()
        try:
            company_id = RuntimeStore(session).get_execution_by_id(execution_id).company_id
            await BusinessWorkflowScheduler(session).run_next_ready(execution_id, company_id)
        finally: session.close()


async def main():
    started = perf_counter(); fixtures = []
    history_a = [3, 5, 2, 6, 4, 7, 3, 8, 4, 9, 5, 10, 6, 11, 7, 12, 8, 13]
    history_b = [0, 8, 0, 11, 0, 7, 0, 12, 0, 9, 0, 13, 0, 10, 0, 14, 0, 15]
    payload = {"items": [{"sku_code": "AGG-A", "demand_history": history_a, "lead_time_days": 14, "initial_stock": 80, "eoq": 25}, {"sku_code": "AGG-B", "demand_history": history_b, "lead_time_days": 21, "initial_stock": 50, "eoq": 20}]}
    try:
        full = create_fixture("complete", payload); fixtures.append(full); await run_steps(full[3], 4)
        session = SessionLocal(); company_id = RuntimeStore(session).get_execution_by_id(full[3]).company_id; store = RuntimeStore(session)
        execution = store.get_execution(full[3], company_id); task_refs = {ref.result_type: ref for ref in store.get_execution_result_references(full[3], company_id)}
        assert execution.state == "completed" and float(execution.progress) == 100 and set(task_refs) == {"forecast", "safety_stock", "simulation", "backtest"}
        attempts_before = session.query(RuntimeTaskAttempt).filter_by(execution_id=full[3]).count(); session.close()

        calls = {"forecast": 0, "safety_stock": 0, "simulation": 0, "backtest": 0}
        originals = (DemandForecaster.forecast, ComprehensiveSafetyStockOptimizer.calculate_all_methods, MonteCarloInventorySimulator.simulate, BacktestEngine.run_backtest)
        def forecast(self, *a, **k): calls["forecast"] += 1; return originals[0](self, *a, **k)
        def safety(self, *a, **k): calls["safety_stock"] += 1; return originals[1](self, *a, **k)
        def simulation(self, *a, **k): calls["simulation"] += 1; return originals[2](self, *a, **k)
        def backtest(self, *a, **k): calls["backtest"] += 1; return originals[3](self, *a, **k)
        DemandForecaster.forecast, ComprehensiveSafetyStockOptimizer.calculate_all_methods, MonteCarloInventorySimulator.simulate, BacktestEngine.run_backtest = forecast, safety, simulation, backtest
        try:
            aggregate = BusinessWorkflowAggregationService().aggregate(company_id, full[3])
            repeated = BusinessWorkflowAggregationService().aggregate(company_id, full[3])
        finally:
            DemandForecaster.forecast, ComprehensiveSafetyStockOptimizer.calculate_all_methods, MonteCarloInventorySimulator.simulate, BacktestEngine.run_backtest = originals
        assert calls == {"forecast": 0, "safety_stock": 0, "simulation": 0, "backtest": 0} and aggregate == repeated
        assert aggregate["forecast"] == task_refs["forecast"].inline_result and aggregate["safety_stock"] == task_refs["safety_stock"].inline_result and aggregate["simulation"] == task_refs["simulation"].inline_result and aggregate["backtest"] == task_refs["backtest"].inline_result
        assert aggregate["provenance"] == {f"{name}_result_reference_id": str(task_refs[name].id) for name in task_refs}
        session = SessionLocal(); company_id = RuntimeStore(session).get_execution_by_id(full[3]).company_id; refs = RuntimeStore(session).get_execution_result_references(full[3], company_id)
        assert len(refs) == 5 and sum(ref.result_type == "business_workflow" and ref.runtime_task_id is None for ref in refs) == 1 and session.query(RuntimeTaskAttempt).filter_by(execution_id=full[3]).count() == attempts_before; session.close()
        # Fresh graph retrieval and idempotent aggregation.
        assert BusinessWorkflowAggregationService().get(company_id, full[3]) == aggregate
        assert BusinessWorkflowAggregationService().aggregate(company_id, full[3]) == aggregate

        partial = create_fixture("partial", payload); fixtures.append(partial); await run_steps(partial[3], 1)
        try: BusinessWorkflowAggregationService().aggregate(partial[1], partial[3]); raise AssertionError("partial workflow aggregated")
        except RuntimeStoreAggregationError: pass
        session = SessionLocal(); assert RuntimeStore(session).get_execution_aggregate_result(partial[3], partial[1]) is None; session.close()

        failed_payload = {"items": [{"sku_code": "FAILED", "demand_history": [1, 2], "lead_time_days": 14, "initial_stock": 20, "eoq": 5}]}
        failed = create_fixture("failed", failed_payload); fixtures.append(failed); await run_steps(failed[3], 1)
        try: BusinessWorkflowAggregationService().aggregate(failed[1], failed[3]); raise AssertionError("failed workflow aggregated")
        except RuntimeStoreAggregationError: pass
        session = SessionLocal(); assert RuntimeStore(session).get_execution_aggregate_result(failed[3], failed[1]) is None; session.close()
        print("PHASE3A5 PASS", json.dumps({"execution_id": str(full[3]), "task_results": 4, "aggregate_results": 1, "attempts": attempts_before, "engine_calls_during_aggregation": calls, "partial_prohibited": True, "failed_prohibited": True, "duration_ms": round((perf_counter() - started) * 1000, 3)}), flush=True)
    finally:
        for fixture in fixtures: cleanup(fixture[0], fixture[1], fixture[2])


if __name__ == "__main__": asyncio.run(main())
