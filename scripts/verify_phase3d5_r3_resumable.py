"""R3 bounded first-use/learned Business Workflow → Decision-plan proof."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_decision_plan import BusinessDecisionPlanService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.company_learning_materialization import CompanyLearningMaterializationService
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.application.decision_snapshot import DecisionSnapshotService
from app.application.pattern_learning_materialization import PatternLearningMaterializationService
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.dataset import Dataset
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.models.supplier_learning_memory import SupplierLearningMemory
from app.services.security import EncryptionService

MATERIAL, DEMAND, CONTEXT, LEVEL = "SKU", "sales", "REPLENISHMENT", "finished_good"


def manifest_path(kind): return Path(__file__).with_name(f".phase3d5_r3_{kind}_manifest.json")
def load(kind): return json.loads(manifest_path(kind).read_text())
def write(kind, value): manifest_path(kind).write_text(json.dumps(value, sort_keys=True, indent=2))
def fp(value): return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def plan_value(plan):
    return {"execution_id": str(plan.execution_id), "company_id": str(plan.company_id), "cutoff": plan.decision_cutoff_period,
        "demand_type": plan.demand_type, "context": plan.decision_context, "materials_total": plan.materials_total,
        "items": list(plan.items), "limitations": list(plan.limitations)}


def learning_counts(session, company_id):
    return {"pattern": session.query(PatternLearningMemory).filter_by(company_id=company_id).count(),
        "company": session.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).count(),
        "supplier": session.query(SupplierLearningMemory).filter_by(company_id=company_id).count(),
        "event": session.query(EventIntelligenceMemory).filter_by(company_id=company_id).count()}


def source_state(session, company_id, execution_id):
    vintage_ids = [row[0] for row in session.query(ForecastVintage.id).filter_by(company_id=company_id)]
    refs = session.query(RuntimeResultReference).filter_by(execution_id=execution_id).all()
    return {"actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
        "actual_revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
        "vintages": len(vintage_ids),
        "vintage_points": session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).count() if vintage_ids else 0,
        "runtime_tasks": session.query(RuntimeTask).filter_by(execution_id=execution_id).count(), "runtime_results": len(refs),
        "result_fingerprints": {ref.result_type: fp(ref.inline_result) for ref in refs},
        "learning": learning_counts(session, company_id),
        "snapshots": session.query(DecisionSnapshot).filter_by(company_id=company_id).count(),
        "snapshot_candidates": session.query(DecisionSnapshotCandidate).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count()}


def actual_values(kind):
    return [100 + (week % 3) for week in range(1, 33)] if kind == "first" else [100] * 28 + [200] * 4


def actual_rows(kind):
    if kind == "first":
        return [(week, value) for week, value in enumerate(actual_values(kind), 1)]
    # The policy's trend-strength normalization is intentionally sample-size
    # sensitive. Eight contiguous terminal weeks give a valid minimum-history
    # structural-change fixture without changing production thresholds.
    return list(zip(range(25, 33), (100, 110, 120, 130, 160, 170, 180, 190)))


async def stage_a(kind):
    assert kind in ("first", "learned") and not manifest_path(kind).exists()
    session = SessionLocal()
    try:
        started = perf_counter(); tag = f"d5r3_{kind}_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag); user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.flush()
        payload = {"items": [{"sku_code": MATERIAL, "demand_history": actual_values(kind), "lead_time_days": 14,
            "initial_stock": 500, "eoq": 100, "product_level": LEVEL}]}
        dataset = Dataset(id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
            dataset_hash=hashlib.sha256((tag + json.dumps(payload)).encode()).hexdigest(), source_type=tag,
            encrypted_data=EncryptionService(session).encrypt_dataset(user.id, payload), is_active=True)
        session.add(dataset); session.commit()
        ActualWeeklyLedgerService().ingest_dataset_actuals(company.id, user.id, dataset.id,
            [{"material_code": MATERIAL, "period": f"2026-W{week:02d}", "quantity": value, "product_level": LEVEL}
             for week, value in actual_rows(kind)], DEMAND)
        assert learning_counts(session, company.id) == {"pattern": 0, "company": 0, "supplier": 0, "event": 0}
        fixture_ms = (perf_counter() - started) * 1000
        accepted = BusinessWorkflowAcceptanceService().accept_or_resolve(company.id, user.id, dataset.id,
            request_metadata={"params": {"forecast_vintage": {"demand_type": DEMAND, "product_metadata": {MATERIAL: {"product_level": LEVEL}}}}})
        workflow_started = perf_counter()
        for _ in range(5):
            session.close(); session = SessionLocal()
            if await BusinessWorkflowScheduler(session).run_next_ready(accepted.execution_id, company.id) is None: break
        execution = session.query(RuntimeExecution).filter_by(execution_id=accepted.execution_id, company_id=company.id).one()
        tasks = session.query(RuntimeTask).filter_by(execution_id=execution.execution_id).order_by(RuntimeTask.task_order).all()
        refs = {ref.result_type: ref for ref in session.query(RuntimeResultReference).filter_by(execution_id=execution.execution_id)}
        assert execution.state == "completed" and float(execution.progress) == 100
        assert [task.task_id for task in tasks] == ["forecast", "safety_stock", "simulation", "backtest"] and set(refs) >= {"forecast", "safety_stock", "simulation", "backtest"}
        attempts = session.query(RuntimeTaskAttempt).filter_by(execution_id=execution.execution_id).all()
        task_ms = {task.task_id: float(next((attempt.duration_ms for attempt in attempts if attempt.runtime_task_id == task.id and attempt.duration_ms is not None), 0) or 0) for task in tasks}
        params = execution.metadata_["request_metadata"]["params"]; cutoff = params["forecast_cutoff_period"]
        demand = params.get("demand_type") or params.get("forecast_vintage", {}).get("demand_type")
        assert demand == DEMAND
        write(kind, {"company_id": str(company.id), "user_id": str(user.id), "dataset_id": str(dataset.id), "execution_id": str(execution.execution_id),
            "material_code": MATERIAL, "demand_type": demand, "cutoff": cutoff, "context": CONTEXT, "product_level": LEVEL})
        print(f"R3 {kind.upper()} WORKFLOW COMPLETE", {"fixture_setup_ms": round(fixture_ms, 3), "analytics_workflow_ms": round((perf_counter() - workflow_started) * 1000, 3),
            "execution_id": str(execution.execution_id), "task_graph": [(task.task_id, list(task.dependencies)) for task in tasks], "cutoff": cutoff,
            "demand_type": demand, "task_duration_ms": task_ms, "learning_counts": learning_counts(session, company.id)}, flush=True)
    finally: session.close()


def stage_l(kind):
    assert kind == "learned"
    manifest = load(kind); company_id = UUID(manifest["company_id"])
    pattern = PatternLearningMaterializationService().materialize(company_id, MATERIAL, DEMAND, manifest["cutoff"])
    company = CompanyLearningMaterializationService().materialize(company_id)
    session = SessionLocal()
    try:
        pattern_row = session.query(PatternLearningMemory).filter_by(company_id=company_id, material_code=MATERIAL, demand_type=DEMAND).one()
        company_row = session.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).one()
        assert pattern.status in {"CREATED", "UNCHANGED"} and company.status in {"CREATED", "UNCHANGED"}
        assert pattern_row.cutoff_period == manifest["cutoff"] and pattern_row.pattern_classification == "STRUCTURAL_CHANGE"
        assert company_row.source_summary_fingerprint == company.source_summary_fingerprint
        manifest.update({"pattern_memory_id": str(pattern_row.id), "pattern_classification": pattern_row.pattern_classification,
            "pattern_fingerprint": pattern_row.source_pattern_fingerprint, "company_memory_id": str(company_row.id),
            "company_maturity": company_row.evidence_maturity_level, "company_fingerprint": company_row.source_summary_fingerprint})
        write(kind, manifest)
        print("R3 LEARNED LEARNING SETUP PASS", {"pattern": {"status": pattern.status, "id": str(pattern_row.id), "classification": pattern_row.pattern_classification,
            "fingerprint": pattern_row.source_pattern_fingerprint, "cutoff": pattern_row.cutoff_period}, "company": {"status": company.status, "id": str(company_row.id),
            "maturity": company_row.evidence_maturity_level, "fingerprint": company_row.source_summary_fingerprint}}, flush=True)
    finally: session.close()


def stage_b(kind):
    manifest = load(kind); company_id, execution_id = UUID(manifest["company_id"]), UUID(manifest["execution_id"])
    session = SessionLocal()
    try:
        execution = session.query(RuntimeExecution).filter_by(execution_id=execution_id, company_id=company_id).one(); assert execution.state == "completed" and float(execution.progress) == 100
        before_graph = tuple((task.task_id, task.state, tuple(task.dependencies)) for task in session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order))
        before = source_state(session, company_id, execution_id)
    finally: session.close()
    total = perf_counter(); started = perf_counter(); envelope = DecisionEvidenceResolver().resolve(company_id, MATERIAL, DEMAND, manifest["cutoff"], CONTEXT); resolver_ms = (perf_counter() - started) * 1000
    started = perf_counter(); policy = DecisionPolicy().evaluate(envelope); policy_ms = (perf_counter() - started) * 1000
    started = perf_counter(); materialization = DecisionSnapshotService().materialize(envelope, policy); snapshot_ms = (perf_counter() - started) * 1000
    started = perf_counter(); plan = BusinessDecisionPlanService().materialize(company_id, execution_id); aggregation_ms = (perf_counter() - started) * 1000
    session = SessionLocal()
    try:
        after_graph = tuple((task.task_id, task.state, tuple(task.dependencies)) for task in session.query(RuntimeTask).filter_by(execution_id=execution_id).order_by(RuntimeTask.task_order))
        after = source_state(session, company_id, execution_id); sources = dict(envelope.required + envelope.optional)
        snapshot = session.query(DecisionSnapshot).filter_by(id=materialization.snapshot_id, company_id=company_id).one(); candidates = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id).order_by(DecisionSnapshotCandidate.ordinal).all()
        assert envelope.status == "READY" and all(sources[name]["status"] == "AVAILABLE" for name in ("forecast", "safety_stock", "simulation", "backtest"))
        if kind == "first": assert all(sources[name]["status"] == "ABSENT" for name in ("pattern", "company_learning", "supplier_learning", "event")) and before["learning"] == after["learning"] == {"pattern": 0, "company": 0, "supplier": 0, "event": 0}
        else: assert sources["pattern"]["status"] == sources["company_learning"]["status"] == "AVAILABLE" and sources["supplier_learning"]["status"] == sources["event"]["status"] == "ABSENT"
        assert before_graph == after_graph and plan.materials_total == 1 and len(plan.items) == 1 and not plan.limitations
        assert plan.items[0]["decision_snapshot_id"] == str(snapshot.id) and plan.demand_type == DEMAND and plan.decision_cutoff_period == manifest["cutoff"]
        assert snapshot.demand_type == DEMAND and snapshot.decision_cutoff_period == manifest["cutoff"] and snapshot.decision_context == CONTEXT
        for key in ("actuals", "actual_revisions", "vintages", "vintage_points", "runtime_tasks", "runtime_results", "result_fingerprints", "learning"):
            assert before[key] == after[key], (key, before[key], after[key])
        assert after["snapshots"] in {before["snapshots"], before["snapshots"] + 1} and after["snapshot_candidates"] in {before["snapshot_candidates"], before["snapshot_candidates"] + len(candidates)}
        semantic = plan_value(plan); manifest.update({"snapshot_id": str(snapshot.id), "candidate_count": len(candidates), "plan_fingerprint": fp(semantic), "policy_fingerprint": snapshot.decision_policy_fingerprint})
        write(kind, manifest); top = policy.candidates[0] if policy.candidates else None
        states = [value.get("status") for value in sources.values()]
        print(f"R3 {kind.upper()} PLAN PASS", {"envelope": envelope.status, "sources": {name: value.get("status") for name, value in sources.items()},
            "evidence_counts": {"available": states.count("AVAILABLE"), "absent": states.count("ABSENT"), "incompatible": states.count("INCOMPATIBLE")},
            "policy": {"candidate_order": [candidate.candidate_type for candidate in policy.candidates], "top": top.candidate_type if top else None,
                "reason_codes": list(top.reason_codes) if top else [], "support": list(policy.supporting_evidence), "conflicts": list(policy.conflicting_evidence), "agreement": policy.agreement_status, "confidence": str(policy.confidence)},
            "snapshot": {"status": materialization.status, "id": str(snapshot.id), "candidate_count": len(candidates), "evidence_fingerprint": snapshot.decision_evidence_fingerprint},
            "plan": semantic, "timing_ms": {"resolver": round(resolver_ms, 3), "policy": round(policy_ms, 3), "snapshot": round(snapshot_ms, 3), "aggregation": round(aggregation_ms, 3), "total": round((perf_counter() - total) * 1000, 3)}}, flush=True)
    finally: session.close()


def stage_c(kind):
    manifest = load(kind); company_id, execution_id = UUID(manifest["company_id"]), UUID(manifest["execution_id"])
    plan = BusinessDecisionPlanService().materialize(company_id, execution_id)
    session = SessionLocal()
    try:
        snapshot = session.query(DecisionSnapshot).filter_by(id=UUID(manifest["snapshot_id"]), company_id=company_id).one(); candidates = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id).order_by(DecisionSnapshotCandidate.ordinal).all()
        assert fp(plan_value(plan)) == manifest["plan_fingerprint"] and len(candidates) == manifest["candidate_count"] and snapshot.decision_policy_fingerprint == manifest["policy_fingerprint"]
        print(f"R3 {kind.upper()} REPEAT PASS", {"snapshot_id": str(snapshot.id), "candidate_count": len(candidates), "plan_fingerprint": manifest["plan_fingerprint"]}, flush=True)
    finally: session.close()


def stage_f():
    manifest = load("learned"); company_id = UUID(manifest["company_id"]); snapshot_id = UUID(manifest["snapshot_id"])
    session = SessionLocal()
    try:
        before = session.query(DecisionSnapshot).filter_by(id=snapshot_id, company_id=company_id).one().source_provenance
        optional_before = dict(before["optional"]); pattern_before, company_before = optional_before["pattern"], optional_before["company_learning"]
        pattern = session.query(PatternLearningMemory).filter_by(id=UUID(manifest["pattern_memory_id"]), company_id=company_id).one()
        pattern.pattern_classification = "STABLE"; pattern.source_pattern_fingerprint = "z" * 64; pattern.row_version += 1; session.commit(); session.expire_all()
        after = session.query(DecisionSnapshot).filter_by(id=snapshot_id, company_id=company_id).one().source_provenance; optional_after = dict(after["optional"])
        assert optional_after["pattern"] == pattern_before and optional_after["company_learning"] == company_before
        assert pattern_before["classification"] == manifest["pattern_classification"] and pattern_before["fingerprint"] == manifest["pattern_fingerprint"]
        print("R3 LEARNED SNAPSHOT FREEZE PASS", {"snapshot_id": str(snapshot_id), "frozen_pattern": pattern_before,
            "frozen_company": company_before, "current_pattern_after_mutation": {"classification": pattern.pattern_classification, "fingerprint": pattern.source_pattern_fingerprint}}, flush=True)
    finally: session.close()


def cleanup(kind):
    manifest = load(kind); company_id = UUID(manifest["company_id"]); session = SessionLocal()
    try:
        execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id)]
        vintage_ids = [row[0] for row in session.query(ForecastVintage.id).filter_by(company_id=company_id)]
        snapshot_ids = [row[0] for row in session.query(DecisionSnapshot.id).filter_by(company_id=company_id)]
        if snapshot_ids: session.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(snapshot_ids)).delete(synchronize_session=False)
        session.query(DecisionSnapshot).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(EventIntelligenceMemory).filter_by(company_id=company_id).delete(synchronize_session=False); session.query(SupplierLearningMemory).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(PatternLearningMemory).filter_by(company_id=company_id).delete(synchronize_session=False); session.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).delete(synchronize_session=False)
        if vintage_ids: session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).delete(synchronize_session=False)
        session.query(ForecastVintage).filter_by(company_id=company_id).delete(synchronize_session=False)
        if execution_ids:
            session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).delete(synchronize_session=False); session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(execution_ids)).delete(synchronize_session=False); session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(execution_ids)).delete(synchronize_session=False); session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False); session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(Dataset).filter_by(id=UUID(manifest["dataset_id"])).delete(synchronize_session=False); session.query(CompanyEncryptionKey).filter_by(user_id=UUID(manifest["user_id"])).delete(synchronize_session=False); session.query(User).filter_by(id=UUID(manifest["user_id"])).delete(synchronize_session=False); session.query(Company).filter_by(id=company_id).delete(synchronize_session=False); session.commit()
        assert session.query(Company).filter_by(id=company_id).count() == 0; print(f"R3 {kind.upper()} CLEANUP PASS", {"residue": 0}, flush=True)
    finally: session.close()
    manifest_path(kind).unlink()


if __name__ == "__main__":
    kind, stage = sys.argv[1:3]
    if stage == "a": asyncio.run(stage_a(kind))
    elif stage == "l": stage_l(kind)
    elif stage == "b": stage_b(kind)
    elif stage == "c": stage_c(kind)
    elif stage == "f" and kind == "learned": stage_f()
    elif stage == "d": cleanup(kind)
    else: raise ValueError("use first/learned with a,l,b,c,d; learned also supports f")
