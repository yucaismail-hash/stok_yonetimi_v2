"""Bounded persisted priority and conflict proofs for ``decision_policy_v1``."""
from pathlib import Path
import sys
from time import perf_counter

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
from scripts.verify_phase3d3a_decision_policy_postgres import T1, build, roots


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


def _evaluate(ids):
    resolver_start = perf_counter()
    envelope = DecisionEvidenceResolver().resolve(ids["company_id"], "SKU", "sales", T1, "REPLENISHMENT")
    resolver_end = perf_counter()
    result = DecisionPolicy().evaluate(envelope)
    policy_end = perf_counter()
    return envelope, result, (resolver_end - resolver_start, policy_end - resolver_end, policy_end - resolver_start)


def _candidate_rows(result):
    return tuple({
        "ordinal": index, "type": candidate.candidate_type, "severity": candidate.severity,
        "priority": candidate.priority, "reasons": candidate.reason_codes,
        "support": candidate.supporting_evidence, "conflicts": candidate.conflicting_evidence,
    } for index, candidate in enumerate(result.candidates, start=1))


def _assert_read_only(ids, before):
    session = SessionLocal()
    try:
        after = _counts(session, ids["company_id"])
    finally:
        session.close()
    assert after == before, {"before": before, "after": after}


def simulation(signal):
    label = "priority_stockout" if signal == "stockout_risk" else "priority_excess"
    started = perf_counter()
    ids = build(label, simulation=signal)
    setup_end = perf_counter()
    session = SessionLocal()
    try:
        before = _counts(session, ids["company_id"])
    finally:
        session.close()
    try:
        envelope, result, times = _evaluate(ids)
        rows = _candidate_rows(result)
        print("PRIORITY SIMULATION DIAGNOSTIC", {
            "signal": signal, "simulation": dict(envelope.optional)["simulation"],
            "candidates": rows, "policy_support": result.supporting_evidence,
            "policy_conflicts": result.conflicting_evidence, "agreement": result.agreement_status,
            "confidence": result.confidence,
        }, flush=True)
        assert dict(envelope.optional)["simulation"]["status"] == "AVAILABLE"
        assert rows == ({"ordinal": 1, "type": "REVIEW_SAFETY_STOCK", "severity": "HIGH", "priority": 10,
                         "reasons": ("SIMULATION_SCENARIO_RISK",), "support": ("simulation",), "conflicts": ()},)
        _assert_read_only(ids, before)
        print("PRIORITY SIMULATION " + signal.upper() + " PASS", {
            "fixture_setup_ms": round((setup_end - started) * 1000, 3),
            "resolver_ms": round(times[0] * 1000, 3), "policy_ms": round(times[1] * 1000, 3),
            "combined_ms": round(times[2] * 1000, 3), "read_only": True,
        }, flush=True)
    finally:
        cleanup = perf_counter()
        d2._cleanup([roots.pop()], [])
        print("PRIORITY SIMULATION " + signal.upper() + " CLEANUP PASS", {"cleanup_ms": round((perf_counter() - cleanup) * 1000, 3), "residue": 0}, flush=True)


def multi_risk():
    started = perf_counter()
    ids = build("priority_multi", supplier="LATE_PRONE", event="POSITIVE_ASSOCIATION", backtest="weak_validation", simulation="stockout_risk")
    setup_end = perf_counter()
    try:
        envelope, result, times = _evaluate(ids)
        rows = _candidate_rows(result)
        session = SessionLocal()
        try:
            before = _counts(session, ids["company_id"])
        finally:
            session.close()
        print("PRIORITY MULTI DIAGNOSTIC", {
            "candidates": rows, "support": result.supporting_evidence, "conflicts": result.conflicting_evidence,
            "agreement": result.agreement_status, "confidence": result.confidence, "fingerprint": result.fingerprint,
        }, flush=True)
        expected_types = ("REVIEW_SAFETY_STOCK", "REVIEW_FORECAST", "REVIEW_SUPPLIER", "MONITOR_EVENT_RISK")
        assert tuple(row["type"] for row in rows) == expected_types
        assert tuple(row["priority"] for row in rows) == (10, 20, 40, 50)
        assert len(set(row["type"] for row in rows)) == len(rows)
        assert result.agreement_status == "CONFLICTED"
        assert result.conflicting_evidence == ("FORECAST_SIGNAL_VS_WEAK_BACKTEST",)
        assert set(result.supporting_evidence) == {
            "BACKTEST_VALIDATION_WEAK", "EVENT_ASSOCIATION_NON_CAUSAL", "SIMULATION_SCENARIO_RISK", "SUPPLIER_LATE_PRONE",
        }
        repeat_envelope, repeat_result, repeat_times = _evaluate(ids)
        assert repeat_envelope == envelope and repeat_result == result
        _assert_read_only(ids, before)

        # Change exactly one compatible source semantics; no timestamps take part in fingerprints.
        session = SessionLocal()
        try:
            session.query(EventIntelligenceMemory).filter_by(
                company_id=ids["company_id"], material_code="SKU", demand_type="sales", event_identity="EVENT"
            ).update({"classification": "NO_CLEAR_EFFECT"})
            session.commit()
            after_mutation = _counts(session, ids["company_id"])
        finally:
            session.close()
        mutated_envelope, mutated_result, mutation_times = _evaluate(ids)
        _assert_read_only(ids, after_mutation)
        mutated_rows = _candidate_rows(mutated_result)
        print("PRIORITY MULTI MUTATION DIAGNOSTIC", {
            "changed_source": "event.classification POSITIVE_ASSOCIATION -> NO_CLEAR_EFFECT",
            "candidates": mutated_rows, "fingerprint": mutated_result.fingerprint,
        }, flush=True)
        assert mutated_result.fingerprint != result.fingerprint
        assert tuple(row["type"] for row in mutated_rows) == expected_types[:-1]
        assert tuple(row["type"] for row in mutated_rows) == tuple(row["type"] for row in rows[:-1])
        print("PRIORITY MULTI PASS", {
            "fixture_setup_ms": round((setup_end - started) * 1000, 3),
            "resolver_ms": round(times[0] * 1000, 3), "policy_ms": round(times[1] * 1000, 3),
            "combined_ms": round(times[2] * 1000, 3), "repeat_combined_ms": round(repeat_times[2] * 1000, 3),
            "semantic_mutation_combined_ms": round(mutation_times[2] * 1000, 3), "read_only": True,
        }, flush=True)
    finally:
        cleanup = perf_counter()
        d2._cleanup([roots.pop()], [])
        print("PRIORITY MULTI CLEANUP PASS", {"cleanup_ms": round((perf_counter() - cleanup) * 1000, 3), "residue": 0}, flush=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "multi"
    if mode == "stockout":
        simulation("stockout_risk")
    elif mode == "excess":
        simulation("excess_risk")
    elif mode == "multi":
        multi_risk()
    else:
        raise SystemExit("mode must be stockout, excess, or multi")
