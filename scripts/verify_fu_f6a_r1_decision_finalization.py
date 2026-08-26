"""Bounded PostgreSQL proof for advisory post-analytics Decision finalization."""
import asyncio
import hashlib
import json
import sys
import threading
from datetime import timedelta
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from uuid_extensions import uuid7

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalizationService
import app.application.business_workflow_decision_finalization as finalization_module
import app.application.business_decision_plan as plan_module
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


class InjectedPreSnapshotError(RuntimeError):
    pass


class InjectedPostSnapshotError(RuntimeError):
    pass


def analytical_state(session, execution_id):
    execution = session.query(RuntimeExecution).filter_by(execution_id=execution_id).one()
    refs = session.query(RuntimeResultReference).filter_by(execution_id=execution_id).order_by(RuntimeResultReference.result_type).all()
    tasks = session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order).all()
    return (
        execution.state, float(execution.progress),
        tuple((task.task_id, task.state) for task in tasks),
        tuple((ref.result_type, str(ref.id), hashlib.sha256(json.dumps(ref.inline_result, sort_keys=True, default=str).encode()).hexdigest()) for ref in refs),
    )


def row(session, execution_id):
    return session.query(BusinessWorkflowDecisionFinalization).filter_by(execution_id=execution_id).one()


def reset_for_retry(session, execution_id):
    value = row(session, execution_id)
    value.status = "failed"
    value.lease_token = None
    value.lease_expires_at = None
    value.finalized_at = None
    value.completed_material_codes = []
    value.limitations = []
    value.last_error = {"code": "PROBE_RESET"}
    session.commit()
    return value.id


MANIFEST = Path(__file__).with_name(".fu_f6a_r1_decision_finalization.json")


def save_manifest(value):
    MANIFEST.write_text(json.dumps(value, sort_keys=True, indent=2), encoding="utf-8")


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def ids(manifest):
    return UUID(manifest["company_id"]), UUID(manifest["user_id"]), UUID(manifest["one_dataset_id"]), UUID(manifest["multi_dataset_id"])


async def drive(execution_id, company_id):
    for _ in range(6):
        session = SessionLocal()
        try:
            if await BusinessWorkflowScheduler(session).run_next_ready(execution_id, company_id) is None:
                break
        finally:
            session.close()


def failing_plan_factory():
    class FailingPlan:
        def materialize(self, company_id, execution_id):
            raise InjectedPreSnapshotError("probe pre-snapshot failure")
    return FailingPlan


def after_snapshot_plan_factory():
    original = plan_module.BusinessDecisionPlanService
    class AfterSnapshot:
        def materialize(self, company_id, execution_id):
            original().materialize(company_id, execution_id)
            raise InjectedPostSnapshotError("probe post-snapshot failure")
    return AfterSnapshot


def selective_policy_factory():
    original = plan_module.DecisionPolicy
    class SelectivePolicy:
        def evaluate(self, envelope):
            if envelope.material_code == "SKU-B":
                raise InjectedPreSnapshotError("probe SKU-B policy failure")
            return original().evaluate(envelope)
    return SelectivePolicy


async def create_dataset(company, user, materials, label):
    session = SessionLocal()
    try:
        payload = {"items": [
            {"sku_code": material, "demand_history": list(range(100, 132)), "lead_time_days": 7,
             "initial_stock": 500, "eoq": 100, "product_level": "finished_good"}
            for material in materials
        ]}
        dataset = Dataset(
            id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
            dataset_hash=hashlib.sha256((label + json.dumps(payload, sort_keys=True)).encode()).hexdigest(),
            source_type=label, encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True,
        )
        session.add(dataset); session.commit()
        ActualWeeklyLedgerService().ingest_dataset_actuals(
            company.id, user.id, dataset.id,
            [{"material_code": material, "period": f"2026-W{week:02d}", "quantity": 100 + week,
              "product_level": "finished_good"} for material in materials for week in range(1, 33)], "sales",
        )
        return dataset.id
    finally:
        session.close()


async def completed_workflow(company, user, dataset_id, materials, patcher=None):
    accepted = BusinessWorkflowAcceptanceService().accept_or_resolve(
        company.id, user.id, dataset_id,
        request_metadata={"params": {"forecast_vintage": {"demand_type": "sales", "product_metadata": {
            material: {"product_level": "finished_good"} for material in materials
        }}}},
    )
    if patcher is None:
        await drive(accepted.execution_id, company.id)
    else:
        with patcher:
            await drive(accepted.execution_id, company.id)
    return accepted.execution_id


async def main():
    session = SessionLocal(); company = user = None; started = perf_counter()
    try:
        tag = "fu_f6a_r1_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.commit()
        one_dataset = await create_dataset(company, user, ["SKU"], tag + "_one")
        multi_dataset = await create_dataset(company, user, ["SKU-A", "SKU-B"], tag + "_multi")

        # A-E: canonical terminal task invokes finalization only after aggregate is committed.
        terminal_started = perf_counter(); success_execution = await completed_workflow(company, user, one_dataset, ["SKU"]); terminal_ms = (perf_counter() - terminal_started) * 1000
        session.expire_all(); before = analytical_state(session, success_execution); success = row(session, success_execution)
        aggregate = session.query(RuntimeResultReference).filter_by(execution_id=success_execution, result_type="business_workflow", runtime_task_id=None).one()
        assert before[0:2] == ("completed", 100.0) and success.status == "succeeded" and success.aggregate_result_reference_id == aggregate.id
        assert [task for task, _ in before[2]] == ["forecast", "safety_stock", "simulation", "backtest"]
        print("F6A-R1 AUTOMATIC SUCCESS PASS", {"execution_id": str(success_execution), "finalization_id": str(success.id), "aggregate_id": str(aggregate.id), "analytics_terminal_ms": round(terminal_ms, 3)}, flush=True)

        # F-G/J: failure/retry is exercised from the same committed analytical
        # execution; no analytical task is rerun merely to retry advisory work.
        reset_for_retry(session, success_execution)
        with patch.object(finalization_module, "BusinessDecisionPlanService", failing_plan_factory()):
            failed = BusinessWorkflowDecisionFinalizationService().finalize(company.id, success_execution)
        session.expire_all(); failed_before = analytical_state(session, success_execution)
        assert failed_before[0] == "completed" and failed.status == "failed" and failed.last_error["error_class"] == "InjectedPreSnapshotError"
        retry_started = perf_counter(); recovered = BusinessWorkflowDecisionFinalizationService().finalize(company.id, success_execution); retry_ms = (perf_counter() - retry_started) * 1000
        session.expire_all(); assert recovered.status == "succeeded" and analytical_state(session, success_execution) == failed_before
        print("F6A-R1 FAILURE RETRY PASS", {"execution_id": str(success_execution), "attempts": recovered.attempt_count, "retry_ms": round(retry_ms, 3)}, flush=True)

        # H: a crash after immutable Snapshot creation leaves lifecycle failed, then reuses it on retry.
        reset_for_retry(session, success_execution)
        snapshots_before = session.query(DecisionSnapshot).filter_by(company_id=company.id, material_code="SKU").count()
        with patch.object(finalization_module, "BusinessDecisionPlanService", after_snapshot_plan_factory()):
            post = BusinessWorkflowDecisionFinalizationService().finalize(company.id, success_execution)
        session.expire_all()
        assert post.status == "failed" and post.last_error["error_class"] == "InjectedPostSnapshotError" and snapshots_before >= 1
        post_recovered = BusinessWorkflowDecisionFinalizationService().finalize(company.id, success_execution)
        session.expire_all(); assert post_recovered.status == "succeeded" and session.query(DecisionSnapshot).filter_by(company_id=company.id, material_code="SKU").count() == snapshots_before
        print("F6A-R1 POST-SNAPSHOT RECOVERY PASS", {"execution_id": str(success_execution), "snapshot_count": snapshots_before}, flush=True)

        # K: per-material policy failure is persisted as partial, then recovered without losing SKU-A.
        partial_execution = await completed_workflow(company, user, multi_dataset, ["SKU-A", "SKU-B"], patch.object(plan_module, "DecisionPolicy", selective_policy_factory()))
        session.expire_all(); partial = row(session, partial_execution)
        assert partial.status == "partially_succeeded" and partial.completed_material_codes == ["SKU-A"] and partial.limitations[0]["material_code"] == "SKU-B"
        partial_recovered = BusinessWorkflowDecisionFinalizationService().finalize(company.id, partial_execution)
        session.expire_all(); assert partial_recovered.status == "succeeded" and set(partial_recovered.completed_material_codes) == {"SKU-A", "SKU-B"}
        print("F6A-R1 PARTIAL RECOVERY PASS", {"execution_id": str(partial_execution), "attempts": partial_recovered.attempt_count}, flush=True)

        # I/J: distinct PostgreSQL sessions allow exactly one concurrent lease owner; expiry is recoverable.
        reset_for_retry(session, success_execution)
        claims = []
        def claim_once():
            claims.append(BusinessWorkflowDecisionFinalizationService().claim(company.id, success_execution))
        threads = [threading.Thread(target=claim_once), threading.Thread(target=claim_once)]
        [thread.start() for thread in threads]; [thread.join() for thread in threads]
        assert sum(claim is not None for claim in claims) == 1
        session.expire_all(); claimed = row(session, success_execution); claimed.lease_expires_at = BusinessWorkflowDecisionFinalizationService._now() - timedelta(seconds=1); session.commit(); session.close(); session = SessionLocal()
        reclaimed = BusinessWorkflowDecisionFinalizationService().recover_due(company.id)
        assert any(result.finalization_id == claimed.id and result.status == "succeeded" for result in reclaimed)
        print("F6A-R1 CONCURRENCY LEASE RECOVERY PASS", {"claim_count": 1, "recovered": len(reclaimed)}, flush=True)

        # P: foreign-key composite ownership rejects a cross-execution aggregate reference.
        first = row(session, success_execution); other_aggregate = row(session, partial_execution).aggregate_result_reference_id
        first.aggregate_result_reference_id = other_aggregate
        try:
            session.flush()
            raise AssertionError("cross-execution aggregate reference was accepted")
        except IntegrityError:
            session.rollback(); session = SessionLocal()
        fresh = BusinessWorkflowDecisionFinalizationService().finalize(company.id, success_execution)
        assert fresh.status == "succeeded"
        print("F6A-R1 AGGREGATE INTEGRITY PASS", {"cross_execution_rejected": True}, flush=True)

        # Fresh-session reconstruction and analytical non-mutation.
        session.close(); session = SessionLocal(); fresh_row = row(session, partial_execution)
        assert fresh_row.status == "succeeded" and fresh_row.aggregate_result_reference_id is not None
        assert analytical_state(session, success_execution) == before
        print("F6A-R1 FRESH SESSION PASS", {"finalization_id": str(fresh_row.id), "elapsed_ms": round((perf_counter() - started) * 1000, 3)}, flush=True)
        print("PHASE FU-F6A-R1 DECISION FINALIZATION PROBE PASS", flush=True)
    finally:
        if session:
            session.rollback()
            if company:
                cid = company.id
                eids = [value[0] for value in session.query(RuntimeExecution.execution_id).filter_by(company_id=cid).all()]
                vids = [value[0] for value in session.query(ForecastVintage.id).filter_by(company_id=cid).all()]
                sids = [value[0] for value in session.query(DecisionSnapshot.id).filter_by(company_id=cid).all()]
                session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(sids)).delete(synchronize_session=False)
                session.query(DecisionSnapshot).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False)
                session.query(ForecastVintage).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(eids)).delete(synchronize_session=False)
                session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(eids)).delete(synchronize_session=False)
                session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(eids)).delete(synchronize_session=False)
                session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(eids)).delete(synchronize_session=False)
                session.query(ActualWeeklyRevision).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(ActualWeeklyObservation).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(Dataset).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(CompanyEncryptionKey).filter_by(user_id=user.id).delete(synchronize_session=False)
                session.query(User).filter_by(id=user.id).delete(synchronize_session=False)
                session.query(Company).filter_by(id=cid).delete(synchronize_session=False)
                session.commit()
                assert session.query(Company).filter_by(id=cid).count() == 0
        if session:
            session.close()


async def shard_a():
    assert not MANIFEST.exists(), "cleanup or resume existing manifest first"
    session = SessionLocal()
    try:
        tag = "fu_f6a_r1_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.commit()
        one_dataset = await create_dataset(company, user, ["SKU"], tag + "_one")
        multi_dataset = await create_dataset(company, user, ["SKU-A", "SKU-B"], tag + "_multi")
        started = perf_counter(); execution_id = await completed_workflow(company, user, one_dataset, ["SKU"]); analytics_ms = (perf_counter() - started) * 1000
        session.expire_all(); finalization = row(session, execution_id); aggregate = session.query(RuntimeResultReference).filter_by(execution_id=execution_id, result_type="business_workflow", runtime_task_id=None).one()
        state = analytical_state(session, execution_id)
        assert state[:2] == ("completed", 100.0) and finalization.status == "succeeded" and finalization.aggregate_result_reference_id == aggregate.id
        assert [task for task, _ in state[2]] == ["forecast", "safety_stock", "simulation", "backtest"]
        save_manifest({"company_id": str(company.id), "user_id": str(user.id), "one_dataset_id": str(one_dataset), "multi_dataset_id": str(multi_dataset), "one_execution_id": str(execution_id), "one_finalization_id": str(finalization.id), "one_aggregate_id": str(aggregate.id), "analytics_ms": analytics_ms})
        print("FU_F6A_R1_A_SUCCESS_COMPLETE", {"execution_id": str(execution_id), "finalization_id": str(finalization.id), "aggregate_id": str(aggregate.id), "analytics_ms": round(analytics_ms, 3)}, flush=True)
    finally:
        session.close()


def shard_b():
    manifest = load_manifest(); company_id, _, _, _ = ids(manifest); execution_id = UUID(manifest["one_execution_id"]); session = SessionLocal()
    try:
        before = analytical_state(session, execution_id); reset_for_retry(session, execution_id)
        with patch.object(finalization_module, "BusinessDecisionPlanService", failing_plan_factory()):
            failed = BusinessWorkflowDecisionFinalizationService().finalize(company_id, execution_id)
        session.expire_all(); failed_row = row(session, execution_id)
        assert failed.status == "failed" and failed_row.last_error["error_class"] == "InjectedPreSnapshotError" and analytical_state(session, execution_id) == before
        recovered = BusinessWorkflowDecisionFinalizationService().finalize(company_id, execution_id)
        session.expire_all(); assert recovered.status == "succeeded" and analytical_state(session, execution_id) == before
        print("FU_F6A_R1_B_FAILURE_RETRY_COMPLETE", {"attempt_count": recovered.attempt_count, "analytics_unchanged": True}, flush=True)
    finally:
        session.close()


def shard_c():
    manifest = load_manifest(); company_id, _, _, _ = ids(manifest); execution_id = UUID(manifest["one_execution_id"]); session = SessionLocal()
    try:
        reset_for_retry(session, execution_id); claims = []
        def once(): claims.append(BusinessWorkflowDecisionFinalizationService().claim(company_id, execution_id))
        threads = (threading.Thread(target=once), threading.Thread(target=once))
        [thread.start() for thread in threads]; [thread.join() for thread in threads]
        winner = next(claim for claim in claims if claim is not None)
        assert sum(claim is not None for claim in claims) == 1
        session.expire_all(); current = row(session, execution_id); current.lease_expires_at = BusinessWorkflowDecisionFinalizationService._now() - timedelta(seconds=1); session.commit(); session.close(); session = SessionLocal()
        recovered = BusinessWorkflowDecisionFinalizationService().recover_due(company_id)
        assert any(result.finalization_id == winner.finalization_id and result.status == "succeeded" for result in recovered)
        print("FU_F6A_R1_C_LEASE_COMPLETE", {"concurrent_owner_count": 1, "expired_lease_reclaimed": True}, flush=True)
    finally:
        session.close()


def shard_d():
    manifest = load_manifest(); company_id, _, _, _ = ids(manifest); execution_id = UUID(manifest["one_execution_id"]); session = SessionLocal()
    try:
        reset_for_retry(session, execution_id); snapshot_count = session.query(DecisionSnapshot).filter_by(company_id=company_id, material_code="SKU").count()
        with patch.object(finalization_module, "BusinessDecisionPlanService", after_snapshot_plan_factory()):
            failed = BusinessWorkflowDecisionFinalizationService().finalize(company_id, execution_id)
        session.expire_all(); assert failed.status == "failed" and row(session, execution_id).last_error["error_class"] == "InjectedPostSnapshotError"
        recovered = BusinessWorkflowDecisionFinalizationService().finalize(company_id, execution_id)
        session.expire_all(); assert recovered.status == "succeeded" and session.query(DecisionSnapshot).filter_by(company_id=company_id, material_code="SKU").count() == snapshot_count
        print("FU_F6A_R1_D_POST_SNAPSHOT_RECOVERY_COMPLETE", {"snapshot_count": snapshot_count, "retry_status": recovered.status}, flush=True)
    finally:
        session.close()


async def shard_e():
    manifest = load_manifest(); company_id, user_id, _, multi_dataset_id = ids(manifest); session = SessionLocal()
    try:
        company = session.query(Company).filter_by(id=company_id).one(); user = session.query(User).filter_by(id=user_id).one()
        execution_id = await completed_workflow(company, user, multi_dataset_id, ["SKU-A", "SKU-B"], patch.object(plan_module, "DecisionPolicy", selective_policy_factory()))
        session.expire_all(); partial = row(session, execution_id); before = analytical_state(session, execution_id)
        assert partial.status == "partially_succeeded" and partial.completed_material_codes == ["SKU-A"] and partial.limitations[0]["material_code"] == "SKU-B"
        recovered = BusinessWorkflowDecisionFinalizationService().finalize(company_id, execution_id)
        session.expire_all(); assert recovered.status == "succeeded" and set(recovered.completed_material_codes) == {"SKU-A", "SKU-B"} and analytical_state(session, execution_id) == before
        manifest["multi_execution_id"] = str(execution_id); manifest["multi_finalization_id"] = str(partial.id); save_manifest(manifest)
        print("FU_F6A_R1_E_PARTIAL_COMPLETE", {"execution_id": str(execution_id), "attempt_count": recovered.attempt_count}, flush=True)
    finally:
        session.close()


def shard_f():
    manifest = load_manifest(); company_id, _, _, _ = ids(manifest); execution_ids = [UUID(manifest["one_execution_id"]), UUID(manifest["multi_execution_id"])]
    session = SessionLocal()
    try:
        rows = [row(session, execution_id) for execution_id in execution_ids]
        assert all(value.status == "succeeded" and value.aggregate_result_reference_id for value in rows)
        assert all(analytical_state(session, execution_id)[:2] == ("completed", 100.0) for execution_id in execution_ids)
        print("FU_F6A_R1_F_FRESH_ZERO_MUTATION_COMPLETE", {"finalizations": [str(value.id) for value in rows], "fresh_session": True}, flush=True)
    finally:
        session.close()


def shard_cleanup():
    manifest = load_manifest(); company_id, user_id, _, _ = ids(manifest); session = SessionLocal()
    try:
        eids = [value[0] for value in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id).all()]
        vids = [value[0] for value in session.query(ForecastVintage.id).filter_by(company_id=company_id).all()]
        sids = [value[0] for value in session.query(DecisionSnapshot.id).filter_by(company_id=company_id).all()]
        session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(sids)).delete(synchronize_session=False)
        session.query(DecisionSnapshot).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vids)).delete(synchronize_session=False)
        session.query(ForecastVintage).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(eids)).delete(synchronize_session=False)
        session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(eids)).delete(synchronize_session=False)
        session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(eids)).delete(synchronize_session=False)
        session.query(RuntimeExecution).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(Dataset).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(CompanyEncryptionKey).filter_by(user_id=user_id).delete(synchronize_session=False)
        session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
        session.query(Company).filter_by(id=company_id).delete(synchronize_session=False)
        session.commit(); assert session.query(Company).filter_by(id=company_id).count() == 0
        MANIFEST.unlink(); print("FU_F6A_R1_G_CLEANUP_COMPLETE", {"residue": 0}, flush=True)
    finally:
        session.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else None
    if mode == "a": asyncio.run(shard_a())
    elif mode == "b": shard_b()
    elif mode == "c": shard_c()
    elif mode == "d": shard_d()
    elif mode == "e": asyncio.run(shard_e())
    elif mode == "f": shard_f()
    elif mode == "cleanup": shard_cleanup()
    else: raise ValueError("use a, b, c, d, e, f, or cleanup")
