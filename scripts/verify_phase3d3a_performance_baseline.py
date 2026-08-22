"""Setup/benchmark/cleanup probe for the 1-SKU Decision pipeline baseline."""
from json import dumps, loads
from pathlib import Path
import statistics
import sys
from time import perf_counter, perf_counter_ns
from uuid import UUID

from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_policy import DecisionPolicy
from app.database import SessionLocal
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.event_observation import EventObservation, EventRevision
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from scripts import verify_phase3d2_decision_evidence_matrix as d2
from scripts.verify_phase3d3a_decision_policy_postgres import T1, build

MANIFEST = Path(__file__).with_name(".phase3d3a_perf_manifest.json")
MATERIAL = "SKU"
DEMAND = "sales"
CONTEXT = "REPLENISHMENT"


def _counts(session, company_id):
    models = (
        ("event_observations", EventObservation), ("event_revisions", EventRevision),
        ("event_memory", EventIntelligenceMemory), ("learning_evidence", LearningEvidence),
        ("learning_delivery", LearningRefreshDelivery), ("runtime_executions", d2.RuntimeExecution),
        ("runtime_references", d2.RuntimeResultReference), ("forecast_vintages", d2.ForecastVintage),
        ("pattern_memory", d2.PatternLearningMemory), ("company_learning", d2.CompanyLearningMemoryV2),
        ("supplier_learning", d2.SupplierLearningMemory), ("retraining_jobs", d2.RetrainingJob),
        ("model_artifacts", d2.ModelArtifact), ("champion_entries", d2.ChampionRegistryEntry),
        ("champion_current", d2.ChampionRegistryCurrent),
    )
    return dict(session.execute(select(*[
        select(func.count()).select_from(model).where(model.company_id == company_id).scalar_subquery().label(name)
        for name, model in models
    ])).one()._mapping)


def _manifest():
    return loads(MANIFEST.read_text(encoding="utf-8"))


def _evaluate(company_id):
    resolver = DecisionEvidenceResolver()
    policy = DecisionPolicy()
    t0 = perf_counter_ns()
    envelope = resolver.resolve(company_id, MATERIAL, DEMAND, T1, CONTEXT)
    t1 = perf_counter_ns()
    result = policy.evaluate(envelope)
    t2 = perf_counter_ns()
    return envelope, result, ((t1 - t0) / 1_000_000, (t2 - t1) / 1_000_000, (t2 - t0) / 1_000_000)


def setup():
    assert not MANIFEST.exists(), "existing benchmark manifest must be cleaned or recovered first"
    started = perf_counter()
    ids = build("performance_baseline", pattern="stable", supplier="LATE_PRONE", event="POSITIVE_ASSOCIATION", backtest="weak_validation", simulation="stockout_risk")
    MANIFEST.write_text(dumps({
        "company_id": str(ids["company_id"]), "material_code": MATERIAL, "demand_type": DEMAND,
        "decision_cutoff_period": T1, "decision_context": CONTEXT,
    }, indent=2), encoding="utf-8")
    print("DECISION PERF SETUP PASS", {"setup_ms": round((perf_counter() - started) * 1000, 3), "manifest": str(MANIFEST)}, flush=True)


def benchmark():
    data = _manifest()
    company_id = UUID(data["company_id"])
    session = SessionLocal()
    try:
        before = _counts(session, company_id)
    finally:
        session.close()
    warm_envelope, warm_result, warm_times = _evaluate(company_id)
    measurements = []
    expected = (warm_envelope.fingerprint, warm_result.fingerprint, warm_result.candidates, warm_result.agreement_status, warm_result.confidence)
    for index in range(1, 6):
        envelope, result, times = _evaluate(company_id)
        assert (envelope.fingerprint, result.fingerprint, result.candidates, result.agreement_status, result.confidence) == expected
        measurements.append(times)
        print("DECISION PERF ITERATION", {"iteration": index, "resolver_ms": round(times[0], 3), "policy_ms": round(times[1], 3), "combined_ms": round(times[2], 3)}, flush=True)
    session = SessionLocal()
    try:
        after = _counts(session, company_id)
    finally:
        session.close()
    assert after == before, {"before": before, "after": after}
    available = absent = incompatible = 0
    for _, value in warm_envelope.required + warm_envelope.optional:
        if value["status"] == "AVAILABLE": available += 1
        elif value["status"] == "ABSENT": absent += 1
        elif value["status"] == "INCOMPATIBLE": incompatible += 1
    stats = {}
    for index, name in enumerate(("resolver", "policy", "combined")):
        values = [item[index] for item in measurements]
        stats[name] = {
            "warmup_ms": round(warm_times[index], 3), "mean_ms": round(statistics.mean(values), 3),
            "median_ms": round(statistics.median(values), 3), "min_ms": round(min(values), 3), "max_ms": round(max(values), 3),
        }
    resolver_mean, policy_mean = stats["resolver"]["mean_ms"], stats["policy"]["mean_ms"]
    total_mean = resolver_mean + policy_mean
    print("DECISION PIPELINE PERFORMANCE BASELINE v1 PASS", {
        "statistics": stats, "source_counts": {"available": available, "absent": absent, "incompatible": incompatible},
        "candidate_count": len(warm_result.candidates), "query_count": "NOT MEASURED",
        "time_distribution_percent": {"resolver": round(100 * resolver_mean / total_mean, 3), "policy": round(100 * policy_mean / total_mean, 3)},
        "read_only": True,
    }, flush=True)


def cleanup():
    data = _manifest()
    company_id = UUID(data["company_id"])
    started = perf_counter()
    d2._cleanup([{"company_id": company_id}], [])
    session = SessionLocal()
    try:
        residue = session.query(d2.Company).filter_by(id=company_id).count()
    finally:
        session.close()
    assert residue == 0
    MANIFEST.unlink()
    print("DECISION PERF CLEANUP PASS", {"cleanup_ms": round((perf_counter() - started) * 1000, 3), "residue": residue, "manifest_removed": not MANIFEST.exists()}, flush=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "benchmark"
    {"setup": setup, "benchmark": benchmark, "cleanup": cleanup}[mode]()
