"""R2 bounded Supplier-present/absent Business Workflow → Decision-plan proof."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter
from uuid import UUID

from uuid_extensions import uuid7

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_decision_plan import BusinessDecisionPlanService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.application.decision_snapshot import DecisionSnapshotService
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService

MATERIAL, CONTEXT = "SKU", "REPLENISHMENT"
CONFIG = {
    "present": {"product_level": "raw_material", "demand_type": "consumption", "supplier": True},
    "absent": {"product_level": "finished_good", "demand_type": "sales", "supplier": False},
}


def manifest_path(kind):
    return Path(__file__).with_name(f".phase3d5_r2_{kind}_manifest.json")


def load(kind):
    return json.loads(manifest_path(kind).read_text())


def write(kind, value):
    manifest_path(kind).write_text(json.dumps(value, sort_keys=True, indent=2))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, default=str, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def plan_value(plan):
    return {"execution_id": str(plan.execution_id), "company_id": str(plan.company_id),
        "cutoff": plan.decision_cutoff_period, "demand_type": plan.demand_type,
        "context": plan.decision_context, "materials_total": plan.materials_total,
        "items": list(plan.items), "limitations": list(plan.limitations)}


def source_state(session, company_id, execution_id):
    vintages = [row[0] for row in session.query(ForecastVintage.id).filter_by(company_id=company_id)]
    refs = session.query(RuntimeResultReference).filter_by(execution_id=execution_id).all()
    return {"actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
        "actual_revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
        "vintages": len(vintages),
        "vintage_points": session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintages)).count() if vintages else 0,
        "runtime_tasks": session.query(RuntimeTask).filter_by(execution_id=execution_id).count(),
        "runtime_results": len(refs),
        "result_fingerprints": {row.result_type: fingerprint(row.inline_result) for row in refs},
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=company_id).count(),
        "snapshot_candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count()}


def supplier_payload():
    return {"suppliers": {"SUP-1": {"name": "Verified Supplier", "delivery_records": [
        {"planned_days_ago": 20, "actual_days_ago": 18, "planned_qty": 100, "actual_qty": 100},
        {"planned_days_ago": 40, "actual_days_ago": 37, "planned_qty": 100, "actual_qty": 98}]}},
        "supplier_mapping": {MATERIAL: {"supplier_id": "SUP-1", "share": 1.0}}}


async def stage_a(kind):
    config = CONFIG[kind]; manifest = manifest_path(kind)
    assert not manifest.exists(), "manifest already exists; resume or clean this scenario"
    session = SessionLocal()
    try:
        started = perf_counter(); tag = f"d5r2_{kind}_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.flush()
        item = {"sku_code": MATERIAL, "demand_history": list(range(100, 132)), "lead_time_days": 14,
            "initial_stock": 500, "eoq": 100, "product_level": config["product_level"]}
        payload = {"items": [item]}
        if config["supplier"]:
            payload.update(supplier_payload())
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
            dataset_hash=hashlib.sha256((tag + json.dumps(payload, sort_keys=True)).encode()).hexdigest(), source_type=tag,
            encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True)
        session.add(dataset); session.commit()
        ActualWeeklyLedgerService().ingest_dataset_actuals(company.id, user.id, dataset.id,
            [{"material_code": MATERIAL, "period": f"2026-W{week:02d}", "quantity": 100 + week,
              "product_level": config["product_level"]} for week in range(1, 33)], config["demand_type"])
        fixture_ms = (perf_counter() - started) * 1000
        accepted = BusinessWorkflowAcceptanceService().accept_or_resolve(company.id, user.id, dataset.id,
            request_metadata={"params": {"forecast_vintage": {"demand_type": config["demand_type"],
                "product_metadata": {MATERIAL: {"product_level": config["product_level"]}}}}})
        analytics_started = perf_counter()
        for _ in range(5):
            session.close(); session = SessionLocal()
            if await BusinessWorkflowScheduler(session).run_next_ready(accepted.execution_id, company.id) is None:
                break
        execution = session.query(RuntimeExecution).filter_by(execution_id=accepted.execution_id, company_id=company.id).one()
        tasks = session.query(RuntimeTask).filter_by(execution_id=execution.execution_id).order_by(RuntimeTask.task_order).all()
        refs = {row.result_type: row for row in session.query(RuntimeResultReference).filter_by(execution_id=execution.execution_id)}
        expected = ["forecast", "supplier", "safety_stock", "simulation", "backtest"] if config["supplier"] else ["forecast", "safety_stock", "simulation", "backtest"]
        assert execution.state == "completed" and float(execution.progress) == 100
        assert [task.task_id for task in tasks] == expected
        assert set(expected).issubset(refs)
        if config["supplier"]:
            assert tasks[1].state == "completed" and refs["supplier"].validation_status == "validated"
            assert refs["supplier"].inline_result.get("suppliers")
        else:
            assert "supplier" not in refs
        point = session.query(ForecastVintagePoint).join(ForecastVintage).filter(
            ForecastVintage.execution_id == execution.execution_id, ForecastVintagePoint.material_code == MATERIAL).first()
        assert point.product_level == config["product_level"]
        attempts = session.query(RuntimeTaskAttempt).filter_by(execution_id=execution.execution_id).all()
        task_ms = {task.task_id: float(next((attempt.duration_ms for attempt in attempts if attempt.runtime_task_id == task.id and attempt.duration_ms is not None), 0) or 0) for task in tasks}
        params = execution.metadata_["request_metadata"]["params"]
        cutoff = params["forecast_cutoff_period"]
        demand = params.get("demand_type") or params.get("forecast_vintage", {}).get("demand_type")
        assert demand == config["demand_type"]
        write(kind, {"company_id": str(company.id), "user_id": str(user.id), "dataset_id": str(dataset.id),
            "execution_id": str(execution.execution_id), "material_code": MATERIAL, "demand_type": demand,
            "product_level": config["product_level"], "cutoff": cutoff, "context": CONTEXT,
            "runtime_task_ids": [str(task.id) for task in tasks], "runtime_result_reference_ids": [str(row.id) for row in refs.values()]})
        print(f"R2 {kind.upper()} WORKFLOW COMPLETE", {"fixture_setup_ms": round(fixture_ms, 3),
            "analytics_workflow_ms": round((perf_counter() - analytics_started) * 1000, 3), "execution_id": str(execution.execution_id),
            "state": execution.state, "progress": float(execution.progress), "task_graph": [(task.task_id, list(task.dependencies)) for task in tasks],
            "cutoff": cutoff, "demand_type": demand, "product_level": point.product_level, "task_duration_ms": task_ms}, flush=True)
    finally:
        session.close()


def stage_b(kind):
    config, manifest = CONFIG[kind], load(kind)
    company_id, execution_id = UUID(manifest["company_id"]), UUID(manifest["execution_id"])
    session = SessionLocal()
    try:
        execution = session.query(RuntimeExecution).filter_by(execution_id=execution_id, company_id=company_id).one()
        assert execution.state == "completed" and float(execution.progress) == 100
        before_graph = tuple((task.task_id, task.state, tuple(task.dependencies)) for task in session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order))
        before = source_state(session, company_id, execution_id)
    finally:
        session.close()
    started = perf_counter(); resolver_started = perf_counter()
    envelope = DecisionEvidenceResolver().resolve(company_id, MATERIAL, manifest["demand_type"], manifest["cutoff"], CONTEXT)
    resolver_ms = (perf_counter() - resolver_started) * 1000
    policy_started = perf_counter(); policy = DecisionPolicy().evaluate(envelope); policy_ms = (perf_counter() - policy_started) * 1000
    snapshot_started = perf_counter(); materialization = DecisionSnapshotService().materialize(envelope, policy); snapshot_ms = (perf_counter() - snapshot_started) * 1000
    aggregation_started = perf_counter(); plan = BusinessDecisionPlanService().materialize(company_id, execution_id); aggregation_ms = (perf_counter() - aggregation_started) * 1000
    session = SessionLocal()
    try:
        after_graph = tuple((task.task_id, task.state, tuple(task.dependencies)) for task in session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order))
        after = source_state(session, company_id, execution_id)
        snapshot = session.query(DecisionSnapshot).filter_by(id=materialization.snapshot_id, company_id=company_id).one()
        candidates = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id).order_by(DecisionSnapshotCandidate.ordinal).all()
        sources = dict(envelope.required + envelope.optional)
        assert envelope.status == "READY" and sources["forecast"]["status"] == "AVAILABLE" and sources["safety_stock"]["status"] == "AVAILABLE"
        assert sources["supplier_operational"]["status"] == ("AVAILABLE" if config["supplier"] else "ABSENT")
        assert sources["supplier_learning"]["status"] == "ABSENT"
        assert before_graph == after_graph and plan.materials_total == 1 and len(plan.items) == 1 and not plan.limitations
        assert plan.items[0]["decision_snapshot_id"] == str(snapshot.id) and plan.demand_type == manifest["demand_type"] and plan.decision_cutoff_period == manifest["cutoff"]
        assert snapshot.demand_type == manifest["demand_type"] and snapshot.decision_cutoff_period == manifest["cutoff"] and snapshot.decision_context == CONTEXT
        assert [row.candidate_type for row in candidates] == [candidate.candidate_type for candidate in policy.candidates]
        for key in ("actuals", "actual_revisions", "vintages", "vintage_points", "runtime_tasks", "runtime_results", "result_fingerprints"):
            assert before[key] == after[key], (key, before[key], after[key])
        assert after["snapshots"] in {before["snapshots"], before["snapshots"] + 1}
        assert after["snapshot_candidates"] in {before["snapshot_candidates"], before["snapshot_candidates"] + len(candidates)}
        semantic = plan_value(plan)
        manifest.update({"snapshot_id": str(snapshot.id), "candidate_count": len(candidates), "policy_fingerprint": snapshot.decision_policy_fingerprint,
            "plan_fingerprint": fingerprint(semantic)})
        write(kind, manifest)
        top = policy.candidates[0] if policy.candidates else None
        print(f"R2 {kind.upper()} PLAN PASS", {"envelope_status": envelope.status,
            "sources": {name: value.get("status") for name, value in sources.items()},
            "policy": {"candidate_order": [candidate.candidate_type for candidate in policy.candidates], "top_candidate": top.candidate_type if top else None,
                "reason_codes": list(top.reason_codes) if top else [], "support": list(policy.supporting_evidence), "conflicts": list(policy.conflicting_evidence),
                "agreement": policy.agreement_status, "confidence": str(policy.confidence), "fingerprint": policy.fingerprint},
            "snapshot": {"status": materialization.status, "id": str(snapshot.id), "candidate_count": len(candidates),
                "evidence_fingerprint": snapshot.decision_evidence_fingerprint, "policy_fingerprint": snapshot.decision_policy_fingerprint},
            "plan": semantic, "timing_ms": {"resolver": round(resolver_ms, 3), "policy": round(policy_ms, 3),
                "snapshot": round(snapshot_ms, 3), "aggregation": round(aggregation_ms, 3), "total_post_analytics": round((perf_counter() - started) * 1000, 3)}}, flush=True)
    finally:
        session.close()


def stage_c(kind):
    manifest = load(kind); company_id, execution_id = UUID(manifest["company_id"]), UUID(manifest["execution_id"])
    plan = BusinessDecisionPlanService().materialize(company_id, execution_id)
    session = SessionLocal()
    try:
        snapshot = session.query(DecisionSnapshot).filter_by(id=UUID(manifest["snapshot_id"]), company_id=company_id).one()
        candidates = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id).order_by(DecisionSnapshotCandidate.ordinal).all()
        assert fingerprint(plan_value(plan)) == manifest["plan_fingerprint"]
        assert plan.items[0]["decision_snapshot_id"] == str(snapshot.id) and len(candidates) == manifest["candidate_count"]
        assert snapshot.decision_policy_fingerprint == manifest["policy_fingerprint"]
        print(f"R2 {kind.upper()} REPEAT PASS", {"snapshot_id": str(snapshot.id), "candidate_count": len(candidates),
            "plan_fingerprint": manifest["plan_fingerprint"]}, flush=True)
    finally:
        session.close()


def cleanup(kind):
    manifest = load(kind); company_id = UUID(manifest["company_id"]); session = SessionLocal()
    try:
        execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id)]
        vintage_ids = [row[0] for row in session.query(ForecastVintage.id).filter_by(company_id=company_id)]
        snapshot_ids = [row[0] for row in session.query(DecisionSnapshot.id).filter_by(company_id=company_id)]
        if snapshot_ids: session.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(snapshot_ids)).delete(synchronize_session=False)
        session.query(DecisionSnapshot).filter_by(company_id=company_id).delete(synchronize_session=False)
        if vintage_ids: session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).delete(synchronize_session=False)
        session.query(ForecastVintage).filter_by(company_id=company_id).delete(synchronize_session=False)
        if execution_ids:
            session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).delete(synchronize_session=False)
            session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(execution_ids)).delete(synchronize_session=False)
            session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(execution_ids)).delete(synchronize_session=False)
            session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(Dataset).filter_by(id=UUID(manifest["dataset_id"])).delete(synchronize_session=False)
        session.query(CompanyEncryptionKey).filter_by(user_id=UUID(manifest["user_id"])).delete(synchronize_session=False)
        session.query(User).filter_by(id=UUID(manifest["user_id"])).delete(synchronize_session=False)
        session.query(Company).filter_by(id=company_id).delete(synchronize_session=False); session.commit()
        assert session.query(Company).filter_by(id=company_id).count() == 0
        print(f"R2 {kind.upper()} CLEANUP PASS", {"company_id": str(company_id), "residue": 0}, flush=True)
    finally:
        session.close()
    manifest_path(kind).unlink()


if __name__ == "__main__":
    scenario, stage = sys.argv[1:3]
    if scenario not in CONFIG: raise ValueError("scenario must be present or absent")
    if stage == "a": asyncio.run(stage_a(scenario))
    elif stage == "b": stage_b(scenario)
    elif stage == "c": stage_c(scenario)
    elif stage == "d": cleanup(scenario)
    else: raise ValueError("stage must be a, b, c, or d")
