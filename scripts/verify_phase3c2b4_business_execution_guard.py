"""PostgreSQL concurrency proof for one active Business Workflow per company."""

import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


def _company(session, token, suffix, users=1):
    company = Company(id=uuid7(), name=f"{token}_{suffix}", tax_id=f"{token}_{suffix}")
    session.add(company)
    session.flush()
    created_users = []
    for index in range(users):
        user = User(id=uuid7(), company_id=company.id, email=f"{token}_{suffix}_{index}@x.invalid", hashed_password="x")
        session.add(user)
        created_users.append(user)
    session.flush()
    return company, created_users


def _dataset(session, company, user, token, suffix, encrypted=True):
    dataset = Dataset(
        id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
        dataset_hash=hashlib.sha256(f"{token}_{suffix}".encode()).hexdigest(), source_type=f"{token}_{suffix}",
        encrypted_data=EncryptionService(session).encrypt_dataset(user.id, {"items": []}) if encrypted else None, is_active=True,
    )
    session.add(dataset)
    return dataset


def _standalone(company_id, user_id, dataset_id, analysis_type):
    session = SessionLocal()
    try:
        execution = RuntimeExecution(
            execution_id=uuid7(), company_id=company_id, user_id=user_id, dataset_id=dataset_id,
            workflow_id=f"standalone-{uuid7()}", analysis_type=analysis_type, state="queued",
            progress=0, current_stage="planning", contract_version="1.0.0", metadata_={},
        )
        capability = "demand_forecast" if analysis_type == "forecast" else analysis_type
        RuntimeStore(session).create_execution(execution, [{
            "workflow_id": execution.workflow_id, "task_id": analysis_type, "capability": capability,
            "task_order": 0, "required": True, "skippable": False, "dependencies": [],
            "state": "pending", "max_attempts": 1, "timeout_seconds": 300,
        }])
        session.commit()
        return execution.execution_id
    finally:
        session.close()


def _terminal(execution_id, company_id, state):
    session = SessionLocal()
    try:
        execution = RuntimeStore(session).get_execution(execution_id, company_id)
        execution.state = state
        session.commit()
    finally:
        session.close()


def _business_count(session, company_id):
    return session.query(RuntimeExecution).filter(
        RuntimeExecution.company_id == company_id,
        RuntimeExecution.analysis_type == "business_workflow",
    ).count()


def main():
    session = SessionLocal()
    company_ids = []
    user_ids = []
    references = []
    try:
        token = "phase3c2b4_" + str(uuid7()).replace("-", "")
        company_a, users_a = _company(session, token, "a", users=2)
        company_b, users_b = _company(session, token, "b")
        company_c, users_c = _company(session, token, "c")
        company_ids.extend((company_a.id, company_b.id, company_c.id))
        user_ids.extend((users_a[0].id, users_a[1].id, users_b[0].id, users_c[0].id))
        dataset_a17 = _dataset(session, company_a, users_a[0], token, "a17")
        dataset_a18 = _dataset(session, company_a, users_a[1], token, "a18", encrypted=False)
        dataset_b = _dataset(session, company_b, users_b[0], token, "b")
        dataset_c = _dataset(session, company_c, users_c[0], token, "c")
        session.commit()
        acceptance = BusinessWorkflowAcceptanceService()

        created = acceptance.accept_or_resolve(company_a.id, users_a[0].id, dataset_a17.id, request_metadata={"source": "ui"})
        same_user = acceptance.accept_or_resolve(company_a.id, users_a[0].id, dataset_a17.id, request_metadata={"source": "ui"})
        cross_user = acceptance.accept_or_resolve(company_a.id, users_a[1].id, dataset_a17.id, request_metadata={"source": "excel"})
        erp = acceptance.accept_or_resolve(company_a.id, users_a[1].id, dataset_a17.id, request_metadata={"source": "erp_api"})
        blocked_v18 = acceptance.accept_or_resolve(company_a.id, users_a[1].id, dataset_a18.id, request_metadata={"source": "erp_api"})
        assert created.status == "CREATED"
        assert all(result.status == "ALREADY_RUNNING" and result.execution_id == created.execution_id for result in (same_user, cross_user, erp, blocked_v18))
        assert blocked_v18.execution_id == created.execution_id

        # Business + standalone and standalone forecast + safety stock stay unconstrained.
        forecast_id = _standalone(company_a.id, users_a[0].id, dataset_a17.id, "forecast")
        safety_id = _standalone(company_a.id, users_a[0].id, dataset_a17.id, "safety_stock")
        assert forecast_id != safety_id

        # Barrier inside two independent sessions makes both requests race at RuntimeStore creation.
        barrier = Barrier(2)
        original_create = RuntimeStore.create_execution

        def gated_create(store, execution, task_rows):
            if execution.analysis_type == "business_workflow" and execution.company_id == company_c.id:
                barrier.wait(timeout=20)
            return original_create(store, execution, task_rows)

        RuntimeStore.create_execution = gated_create
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(acceptance.accept_or_resolve, company_c.id, users_c[0].id, dataset_c.id, "1.0.0", {"source": source})
                    for source in ("ui", "erp_api")
                ]
                concurrent = [future.result(timeout=45) for future in futures]
        finally:
            RuntimeStore.create_execution = original_create
        assert {result.status for result in concurrent} == {"CREATED", "ALREADY_RUNNING"}
        assert concurrent[0].execution_id == concurrent[1].execution_id

        company_b_result = acceptance.accept_or_resolve(company_b.id, users_b[0].id, dataset_b.id, request_metadata={"source": "ui"})
        assert company_b_result.status == "CREATED"

        # Each terminal state releases the partial-index predicate without manual lock cleanup.
        _terminal(created.execution_id, company_a.id, "completed")
        rerun_completed = acceptance.accept_or_resolve(company_a.id, users_a[1].id, dataset_a18.id)
        _terminal(rerun_completed.execution_id, company_a.id, "failed")
        rerun_failed = acceptance.accept_or_resolve(company_a.id, users_a[0].id, dataset_a17.id)
        _terminal(rerun_failed.execution_id, company_a.id, "cancelled")
        rerun_cancelled = acceptance.accept_or_resolve(company_a.id, users_a[1].id, dataset_a18.id)
        assert all(result.status == "CREATED" for result in (rerun_completed, rerun_failed, rerun_cancelled))

        fresh = BusinessWorkflowAcceptanceService().accept_or_resolve(company_a.id, users_a[0].id, dataset_a17.id)
        assert fresh.status == "ALREADY_RUNNING" and fresh.execution_id == rerun_cancelled.execution_id

        session.close()
        session = SessionLocal()
        assert _business_count(session, company_a.id) == 4
        assert _business_count(session, company_b.id) == 1
        assert _business_count(session, company_c.id) == 1
        active_a = session.query(RuntimeExecution).filter(
            RuntimeExecution.company_id == company_a.id, RuntimeExecution.analysis_type == "business_workflow",
            RuntimeExecution.state.in_(("created", "queued", "running", "waiting", "retrying")),
        ).count()
        graph_tasks = session.query(RuntimeTask).filter_by(execution_id=created.execution_id).count()
        assert active_a == 1 and graph_tasks in (4, 5)
        assert session.query(RuntimeTask).filter_by(execution_id=concurrent[0].execution_id).count() in (4, 5)
        assert session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.company_id.in_(company_ids)).count() == 0
        assert session.query(RuntimeResultReference).filter(RuntimeResultReference.company_id.in_(company_ids)).count() == 0
        print("PHASE3C2B4-B PASS", {"same_execution": str(created.execution_id), "task_count": graph_tasks, "concurrent_statuses": sorted(result.status for result in concurrent), "business_a": 4})
    finally:
        if company_ids:
            session.rollback()
            execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter(RuntimeExecution.company_id.in_(company_ids)).all()]
            if execution_ids:
                session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
            session.query(Dataset).filter(Dataset.company_id.in_(company_ids)).delete(synchronize_session=False)
            session.query(CompanyEncryptionKey).filter(CompanyEncryptionKey.user_id.in_(user_ids)).delete(synchronize_session=False)
            session.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
            session.query(Company).filter(Company.id.in_(company_ids)).delete(synchronize_session=False)
            session.commit()
            assert session.query(Company).filter(Company.id.in_(company_ids)).count() == 0
        session.close()


if __name__ == "__main__":
    main()
