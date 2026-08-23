"""R1B manifest-backed stages: workflow | plan | repeat | cleanup.

Run one bounded stage per process. The manifest has fixture-owned primitive
values only, so an interrupted proof can resume safely.
"""
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

MANIFEST = Path(__file__).with_name(".phase3d5_r1_manifest.json")
MATERIAL, DEMAND_TYPE, CONTEXT = "SKU", "sales", "REPLENISHMENT"


def _load_manifest():
    return json.loads(MANIFEST.read_text())


def _write_manifest(value):
    MANIFEST.write_text(json.dumps(value, sort_keys=True, indent=2))


def _semantic_plan(plan):
    return {"execution_id": str(plan.execution_id), "company_id": str(plan.company_id),
        "decision_cutoff_period": plan.decision_cutoff_period, "demand_type": plan.demand_type,
        "decision_context": plan.decision_context, "materials_total": plan.materials_total,
        "items": list(plan.items), "limitations": list(plan.limitations)}


def _fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _source_counts(session, company_id):
    execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id)]
    vintage_ids = [row[0] for row in session.query(ForecastVintage.id).filter_by(company_id=company_id)]
    return {"actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
        "actual_revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
        "vintages": len(vintage_ids),
        "vintage_points": session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).count() if vintage_ids else 0,
        "runtime_results": session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).count() if execution_ids else 0,
        "runtime_tasks": session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(execution_ids)).count() if execution_ids else 0,
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=company_id).count(),
        "snapshot_candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count()}


async def stage_a():
    assert not MANIFEST.exists(), "manifest already exists; resume or run cleanup"
    session = SessionLocal()
    try:
        started = perf_counter(); tag = "d5r1b_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.flush()
        payload = {"items": [{"sku_code": MATERIAL, "demand_history": list(range(100, 132)), "lead_time_days": 7, "initial_stock": 500, "eoq": 100, "product_level": "finished_good"}]}
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
            dataset_hash=hashlib.sha256(tag.encode()).hexdigest(), source_type=tag,
            encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True)
        session.add(dataset); session.commit()
        ActualWeeklyLedgerService().ingest_dataset_actuals(company.id, user.id, dataset.id,
            [{"material_code": MATERIAL, "period": f"2026-W{week:02d}", "quantity": 100 + week,
              "product_level": "finished_good"} for week in range(1, 33)], DEMAND_TYPE)
        fixture_ms = (perf_counter() - started) * 1000
        accepted = BusinessWorkflowAcceptanceService().accept_or_resolve(company.id, user.id, dataset.id,
            request_metadata={"params": {"forecast_vintage": {"demand_type": DEMAND_TYPE,
                "product_metadata": {MATERIAL: {"product_level": "finished_good"}}}}})
        workflow_started = perf_counter()
        for _ in range(5):
            session.close(); session = SessionLocal()
            outcome = await BusinessWorkflowScheduler(session).run_next_ready(accepted.execution_id, company.id)
            if outcome is None:
                break
        execution = session.query(RuntimeExecution).filter_by(execution_id=accepted.execution_id, company_id=company.id).one()
        tasks = session.query(RuntimeTask).filter_by(execution_id=execution.execution_id).order_by(RuntimeTask.task_order).all()
        references = session.query(RuntimeResultReference).filter_by(execution_id=execution.execution_id).all()
        assert execution.state == "completed" and float(execution.progress) == 100
        assert [task.task_id for task in tasks] == ["forecast", "safety_stock", "simulation", "backtest"]
        assert {ref.result_type for ref in references} >= {"forecast", "safety_stock", "simulation", "backtest"}
        attempts = session.query(RuntimeTaskAttempt).filter_by(execution_id=execution.execution_id).all()
        task_ms = {task.task_id: float(next((attempt.duration_ms for attempt in attempts if attempt.runtime_task_id == task.id and attempt.duration_ms is not None), 0) or 0) for task in tasks}
        params = execution.metadata_["request_metadata"]["params"]
        cutoff = params["forecast_cutoff_period"]
        demand = params.get("demand_type") or params.get("forecast_vintage", {}).get("demand_type")
        assert demand == DEMAND_TYPE
        _write_manifest({"company_id": str(company.id), "user_id": str(user.id), "dataset_id": str(dataset.id),
            "runtime_execution_id": str(execution.execution_id), "material_code": MATERIAL, "demand_type": demand,
            "workflow_cutoff": cutoff, "decision_context": CONTEXT,
            "runtime_task_ids": [str(task.id) for task in tasks],
            "runtime_result_reference_ids": [str(ref.id) for ref in references]})
        print("R1 WORKFLOW COMPLETE", {"fixture_setup_ms": round(fixture_ms, 3),
            "analytics_workflow_ms": round((perf_counter() - workflow_started) * 1000, 3),
            "execution_id": str(execution.execution_id), "state": execution.state, "progress": float(execution.progress),
            "cutoff": cutoff, "demand_type": demand, "task_graph": [(task.task_id, list(task.dependencies)) for task in tasks],
            "task_duration_ms": task_ms, "supplier": "ABSENT / not executed in R1"}, flush=True)
    finally:
        session.close()


def stage_b():
    manifest = _load_manifest(); company_id, execution_id = UUID(manifest["company_id"]), UUID(manifest["runtime_execution_id"])
    session = SessionLocal()
    try:
        execution = session.query(RuntimeExecution).filter_by(execution_id=execution_id, company_id=company_id).one()
        assert execution.state == "completed" and float(execution.progress) == 100
        assert manifest["workflow_cutoff"] and manifest["demand_type"] == DEMAND_TYPE
        before_graph = tuple((task.task_id, task.state, tuple(task.dependencies)) for task in session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order))
        before_counts = _source_counts(session, company_id)
    finally:
        session.close()
    started = perf_counter(); resolver = DecisionEvidenceResolver()
    resolver_started = perf_counter(); envelope = resolver.resolve(company_id, MATERIAL, DEMAND_TYPE, manifest["workflow_cutoff"], CONTEXT); resolver_ms = (perf_counter() - resolver_started) * 1000
    policy_started = perf_counter(); policy = DecisionPolicy().evaluate(envelope); policy_ms = (perf_counter() - policy_started) * 1000
    snapshot_started = perf_counter(); snapshot_result = DecisionSnapshotService().materialize(envelope, policy); snapshot_ms = (perf_counter() - snapshot_started) * 1000
    plan_started = perf_counter(); plan = BusinessDecisionPlanService().materialize(company_id, execution_id); plan_ms = (perf_counter() - plan_started) * 1000
    session = SessionLocal()
    try:
        after_graph = tuple((task.task_id, task.state, tuple(task.dependencies)) for task in session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order))
        after_counts = _source_counts(session, company_id)
        snapshot = session.query(DecisionSnapshot).filter_by(id=snapshot_result.snapshot_id, company_id=company_id).one()
        candidates = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id).order_by(DecisionSnapshotCandidate.ordinal).all()
        semantic_plan = _semantic_plan(plan)
        assert before_graph == after_graph
        assert plan.materials_total == 1 and len(plan.items) == 1 and not plan.limitations
        assert plan.items[0]["material_code"] == MATERIAL and plan.items[0]["decision_snapshot_id"] == str(snapshot.id)
        assert snapshot.demand_type == DEMAND_TYPE and snapshot.decision_context == CONTEXT and snapshot.decision_cutoff_period == manifest["workflow_cutoff"]
        assert [row.candidate_type for row in candidates] == [candidate.candidate_type for candidate in policy.candidates]
        for key in ("actuals", "actual_revisions", "vintages", "vintage_points", "runtime_results", "runtime_tasks"):
            assert before_counts[key] == after_counts[key], (key, before_counts[key], after_counts[key])
        assert after_counts["snapshots"] in {before_counts["snapshots"], before_counts["snapshots"] + 1}
        assert after_counts["snapshot_candidates"] in {before_counts["snapshot_candidates"], before_counts["snapshot_candidates"] + len(candidates)}
        manifest.update({"decision_snapshot_id": str(snapshot.id), "decision_snapshot_candidate_count": len(candidates),
            "decision_policy_fingerprint": snapshot.decision_policy_fingerprint, "plan_semantic_fingerprint": _fingerprint(semantic_plan)})
        _write_manifest(manifest)
        sources = dict(envelope.required + envelope.optional); top = policy.candidates[0] if policy.candidates else None
        print("R1 PLAN PASS", {"envelope_status": envelope.status, "decision_context": envelope.decision_context,
            "cutoff": envelope.decision_cutoff_period, "demand_type": envelope.demand_type,
            "sources": {name: value.get("status") for name, value in sources.items()},
            "policy": {"candidate_order": [candidate.candidate_type for candidate in policy.candidates], "top_candidate": top.candidate_type if top else None,
                "reason_codes": list(top.reason_codes) if top else [], "supporting_evidence": list(policy.supporting_evidence),
                "conflicting_evidence": list(policy.conflicting_evidence), "agreement": policy.agreement_status,
                "confidence": str(policy.confidence), "fingerprint": policy.fingerprint},
            "snapshot": {"status": snapshot_result.status, "id": str(snapshot.id), "candidate_count": len(candidates),
                "evidence_fingerprint": snapshot.decision_evidence_fingerprint, "policy_fingerprint": snapshot.decision_policy_fingerprint},
            "plan": semantic_plan, "timing_ms": {"resolver": round(resolver_ms, 3), "policy": round(policy_ms, 3),
                "snapshot": round(snapshot_ms, 3), "aggregation": round(plan_ms, 3), "total_post_analytics": round((perf_counter() - started) * 1000, 3)},
            "source_counts_before": before_counts, "source_counts_after": after_counts}, flush=True)
    finally:
        session.close()


def stage_c():
    manifest = _load_manifest(); company_id, execution_id = UUID(manifest["company_id"]), UUID(manifest["runtime_execution_id"])
    plan = BusinessDecisionPlanService().materialize(company_id, execution_id)
    session = SessionLocal()
    try:
        snapshot = session.query(DecisionSnapshot).filter_by(id=UUID(manifest["decision_snapshot_id"]), company_id=company_id).one()
        candidates = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id).order_by(DecisionSnapshotCandidate.ordinal).all()
        assert _fingerprint(_semantic_plan(plan)) == manifest["plan_semantic_fingerprint"]
        assert plan.items[0]["decision_snapshot_id"] == str(snapshot.id)
        assert len(candidates) == manifest["decision_snapshot_candidate_count"]
        assert snapshot.decision_policy_fingerprint == manifest["decision_policy_fingerprint"]
        print("R1 PLAN REPEAT PASS", {"execution_id": str(execution_id), "snapshot_id": str(snapshot.id),
            "candidate_count": len(candidates), "plan_semantic_fingerprint": manifest["plan_semantic_fingerprint"]}, flush=True)
    finally:
        session.close()


def cleanup():
    manifest = _load_manifest(); company_id = UUID(manifest["company_id"]); session = SessionLocal()
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
        print("R1 CLEANUP PASS", {"company_id": str(company_id), "residue": 0}, flush=True)
    finally:
        session.close()
    MANIFEST.unlink()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "a": asyncio.run(stage_a())
    elif mode == "b": stage_b()
    elif mode == "c": stage_c()
    elif mode == "d": cleanup()
    else: raise ValueError("usage: a | b | c | d")
