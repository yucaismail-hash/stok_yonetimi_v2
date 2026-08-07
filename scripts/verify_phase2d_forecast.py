"""Development-only proof for the durable real standalone Forecast vertical slice."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7
from sqlalchemy.orm import configure_mappers

from app.application.workflow_dispatcher import WorkflowDispatcher
from app.database import SessionLocal
from app.engine.local_forecast_runner import LocalForecastRunner
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


async def main():
    session = SessionLocal()
    probe = "phase2d_fast2_" + str(uuid7()).replace("-", "")
    company = user = dataset = None
    try:
        configure_mappers()
        company = Company(id=uuid7(), name=probe, tax_id=probe)
        user = User(id=uuid7(), company_id=company.id, email=probe + "@example.invalid", hashed_password="probe")
        session.add_all((company, user)); session.flush()
        payload = {"items": [
            {"sku_code": "SKU_A", "demand_history": [10,11,12,13,14,15,16,17,18,19,20,21]},
            {"sku_code": "SKU_B", "demand_history": [2,9,3,11,4,8,5,12,6,7,9,13]},
        ]}
        encrypted = EncryptionService(session).encrypt_dataset(user.id, payload)
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
            dataset_hash=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            source_type=probe, encrypted_data=encrypted, is_active=True)
        session.add(dataset); session.commit()

        dispatcher = WorkflowDispatcher()
        started = perf_counter()
        accepted = await dispatcher.dispatch_single_analysis(company.id, user.id, dataset.id, "forecast", params={"horizon": 4})
        acceptance_ms = (perf_counter() - started) * 1000
        execution_id = accepted["execution_id"]
        durable = session.query(RuntimeExecution).filter_by(execution_id=execution_id).one()
        tasks = session.query(RuntimeTask).filter_by(execution_id=execution_id).all()
        assert durable.state == "queued" and float(durable.progress) == 0 and len(tasks) == 1
        assert tasks[0].capability == "demand_forecast" and tasks[0].state == "pending" and tasks[0].required and not tasks[0].skippable and tasks[0].dependencies == []
        execution_started = perf_counter()
        await LocalForecastRunner().run(execution_id)
        execution_ms = (perf_counter() - execution_started) * 1000

        # New graph proves reads are durable and independent of dispatcher's in-memory context.
        fresh = WorkflowDispatcher()
        status = await fresh.get_execution_status(execution_id)
        result = await fresh.get_execution_result(execution_id)
        session.expire_all(); durable = session.query(RuntimeExecution).filter_by(execution_id=execution_id).one()
        task = session.query(RuntimeTask).filter_by(execution_id=execution_id).one()
        attempts = session.query(RuntimeTaskAttempt).filter_by(execution_id=execution_id).all()
        refs = session.query(RuntimeResultReference).filter_by(execution_id=execution_id).all()
        assert status["state"] == "completed" and status["progress"] == 100
        assert durable.state == "completed" and float(durable.progress) == 100 and task.state == "completed" and len(attempts) == 1 and attempts[0].state == "completed"
        assert len(refs) == 1 and refs[0].validation_status == "validated" and result["result"] == refs[0].inline_result
        assert len(result["result"]["items"]) == 2 and result["result"]["horizon"] == 4

        failed = await dispatcher.dispatch_single_analysis(company.id, user.id, dataset.id, "forecast", params={"horizon": 0})
        failed_id = failed["execution_id"]
        await LocalForecastRunner().run(failed_id)
        session.expire_all(); failed_execution = session.query(RuntimeExecution).filter_by(execution_id=failed_id).one()
        failed_task = session.query(RuntimeTask).filter_by(execution_id=failed_id).one()
        failed_attempt = session.query(RuntimeTaskAttempt).filter_by(execution_id=failed_id).one()
        assert failed_execution.state == "failed" and failed_task.state == "failed" and failed_attempt.state == "failed"
        assert session.query(RuntimeResultReference).filter_by(execution_id=failed_id).count() == 0
        print("PHASE2D FAST2 PASS", json.dumps({
            "acceptance_latency_ms": round(acceptance_ms, 3), "forecast_execution_duration_ms": round(execution_ms, 3),
            "total_duration_ms": round((perf_counter()-started)*1000, 3), "sku_count": 2, "horizon": 4,
            "attempt_count": len(attempts), "execution_id": str(execution_id), "failure_execution_id": str(failed_id),
        }), flush=True)
    finally:
        session.rollback()
        if company is not None:
            # Only rows rooted in this exact synthetic company are removed.
            ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=company.id).all()]
            if ids:
                session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(ids)).delete(synchronize_session=False)
                session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(ids)).delete(synchronize_session=False)
                session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(ids)).delete(synchronize_session=False)
                session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(ids)).delete(synchronize_session=False)
            session.query(Dataset).filter_by(source_type=probe).delete(synchronize_session=False)
            session.query(CompanyEncryptionKey).filter_by(user_id=user.id).delete(synchronize_session=False)
            session.query(User).filter_by(email=probe + "@example.invalid").delete(synchronize_session=False)
            session.query(Company).filter_by(tax_id=probe).delete(synchronize_session=False)
            session.commit()
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
