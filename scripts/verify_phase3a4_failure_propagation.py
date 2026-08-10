"""Real PostgreSQL failure-propagation probe for the four-task Business Workflow."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

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
    session = SessionLocal(); execution = RuntimeStore(session).get_execution_by_id(execution_id)
    assert execution is not None
    return session, execution.company_id


async def scenario(name, payload, failed_task, completed_tasks):
    probe = "phase3a4_" + name + "_" + str(uuid7()).replace("-", "")
    session = SessionLocal(); company_id = user_id = None; started = perf_counter()
    try:
        company = Company(id=uuid7(), name=probe, tax_id=probe); company_id = company.id
        user = User(id=uuid7(), company_id=company_id, email=probe + "@example.invalid", hashed_password="probe"); user_id = user.id
        session.add_all((company, user)); session.flush()
        dataset = Dataset(id=uuid7(), company_id=company_id, user_id=user_id, uploaded_by=user_id, dataset_hash=hashlib.sha256(json.dumps(payload).encode()).hexdigest(), source_type=probe, encrypted_data=EncryptionService(session).encrypt_dataset(user_id, payload), is_active=True)
        session.add(dataset); session.commit()
        execution_id = BusinessWorkflowAcceptanceService().accept(company_id, user_id, dataset.id, request_metadata={"params": {"n_simulations": 6, "weeks": 3, "test_window": 12}})
        session.close(); session = None
        for _ in range(len(completed_tasks) + 1):
            session, recovered_company_id = fresh(execution_id)
            await BusinessWorkflowScheduler(session).run_next_ready(execution_id, recovered_company_id)
            session.close(); session = None

        # The failure is read using an entirely new graph and only execution_id.
        session, recovered_company_id = fresh(execution_id); store = RuntimeStore(session)
        execution = store.get_execution(execution_id, recovered_company_id); tasks = {task.task_id: task for task in store.get_tasks(execution_id, recovered_company_id)}; refs = store.get_execution_result_references(execution_id, recovered_company_id)
        assert execution.state == "failed" and execution.current_stage == failed_task and float(execution.progress) == 25 * len(completed_tasks)
        assert all(tasks[name].state == "completed" for name in completed_tasks) and tasks[failed_task].state == "failed"
        blocked = set(tasks) - set(completed_tasks) - {failed_task}
        assert all(tasks[name].state == "pending" for name in blocked)
        assert {ref.result_type for ref in refs} == set(completed_tasks) and all(ref.validation_status == "validated" for ref in refs)
        assert not any(row["ready"] for row in BusinessWorkflowScheduler(session).readiness(execution_id, recovered_company_id))
        before_attempts = session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id).count(); before_results = len(refs)
        assert await BusinessWorkflowScheduler(session).run_next_ready(execution_id, recovered_company_id) is None
        assert session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id).count() == before_attempts and len(store.get_execution_result_references(execution_id, recovered_company_id)) == before_results
        assert session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id, runtime_task_id=tasks[failed_task].id, state="failed").count() == 1
        print("PHASE3A4 SCENARIO PASS", json.dumps({"scenario": name, "execution_id": str(execution_id), "failed_task": failed_task, "completed_tasks": completed_tasks, "blocked_pending": sorted(blocked), "progress": float(execution.progress), "attempts": before_attempts, "validated_results": before_results, "duration_ms": round((perf_counter() - started) * 1000, 3)}), flush=True)
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


async def main():
    history = [3, 5, 2, 6, 4, 7, 3, 8, 4, 9, 5, 10, 6, 11, 7, 12]
    await scenario("forecast", {"items": [{"sku_code": "BAD-FORECAST", "demand_history": [1, 2], "lead_time_days": 14, "initial_stock": 20, "eoq": 5}]}, "forecast", [])
    await scenario("safety_stock", {"items": [{"sku_code": "BAD-SAFETY", "demand_history": history, "initial_stock": 20, "eoq": 5}]}, "safety_stock", ["forecast"])
    await scenario("simulation", {"items": [{"sku_code": "BAD-SIM", "demand_history": history, "lead_time_days": 14, "initial_stock": 20}]}, "simulation", ["forecast", "safety_stock"])
    await scenario("backtest", {"items": [{"sku_code": "BAD-BACKTEST", "demand_history": history[:12], "lead_time_days": 14, "initial_stock": 20, "eoq": 5}]}, "backtest", ["forecast", "safety_stock", "simulation"])
    print("PHASE3A4 PASS", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
