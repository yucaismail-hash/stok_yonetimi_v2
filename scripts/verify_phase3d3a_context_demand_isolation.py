"""Two bounded PostgreSQL proofs that Decision evidence never crosses demand scopes."""
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
            ("event_observations", EventObservation),
            ("event_revisions", EventRevision),
            ("event_memory", EventIntelligenceMemory),
            ("learning_evidence", LearningEvidence),
            ("learning_delivery", LearningRefreshDelivery),
            ("runtime_executions", d2.RuntimeExecution),
            ("runtime_references", d2.RuntimeResultReference),
            ("forecast_vintages", d2.ForecastVintage),
            ("pattern_memory", d2.PatternLearningMemory),
            ("company_learning", d2.CompanyLearningMemoryV2),
            ("supplier_learning", d2.SupplierLearningMemory),
            ("retraining_jobs", d2.RetrainingJob),
            ("model_artifacts", d2.ModelArtifact),
            ("champion_entries", d2.ChampionRegistryEntry),
            ("champion_current", d2.ChampionRegistryCurrent),
    )
    columns = [
        select(func.count()).select_from(model).where(model.company_id == company_id).scalar_subquery().label(name)
        for name, model in models
    ]
    return dict(session.execute(select(*columns)).one()._mapping)


def _resolve(ids, demand):
    resolver_start = perf_counter()
    envelope = DecisionEvidenceResolver().resolve(ids["company_id"], "SKU", demand, T1, "REPLENISHMENT")
    resolver_end = perf_counter()
    result = DecisionPolicy().evaluate(envelope)
    policy_end = perf_counter()
    return envelope, result, (resolver_end - resolver_start, policy_end - resolver_end, policy_end - resolver_start)


def _identity(envelope, result, requested, persisted):
    optional = dict(envelope.optional)
    return {
        "requested_demand_type": requested,
        "persisted_actionable_demand_type": persisted,
        "event": optional["event"],
        "simulation": optional["simulation"],
        "candidate_types": tuple(candidate.candidate_type for candidate in result.candidates),
        "reason_codes": tuple(code for candidate in result.candidates for code in candidate.reason_codes),
        "policy_fingerprint": result.fingerprint,
    }


def _assert_read_only(ids, before):
    session = SessionLocal()
    try:
        after = _counts(session, ids["company_id"])
    finally:
        session.close()
    assert after == before, {"before": before, "after": after}


def sales_to_consumption():
    started = perf_counter()
    # Sales has the only actionable Event and runtime simulation signal.
    ids = build("context_demand_sales_to_consumption", event="POSITIVE_ASSOCIATION")
    session = SessionLocal()
    try:
        d2._runtime(session, ids, "SKU", "sales", T1, "simulation", "stockout_risk")
        d2._forecast(session, ids, "SKU", "consumption", T1, "finished_good")
        d2._runtime(session, ids, "SKU", "consumption", T1, "safety_stock")
        session.commit()
        persisted_event = session.query(EventIntelligenceMemory).filter_by(
            company_id=ids["company_id"], material_code="SKU", demand_type="sales"
        ).one()
        before = _counts(session, ids["company_id"])
    finally:
        session.close()
    setup_end = perf_counter()
    try:
        own_envelope, own_result, _ = _resolve(ids, "sales")
        envelope, result, timings = _resolve(ids, "consumption")
        print("CONTEXT D3-A DIAGNOSTIC", {
            "sales_control": _identity(own_envelope, own_result, "sales", "sales"),
            "consumption_cross_scope": _identity(envelope, result, "consumption", "sales"),
            "persisted_event_id": str(persisted_event.id),
        }, flush=True)
        own_types = tuple(candidate.candidate_type for candidate in own_result.candidates)
        cross_types = tuple(candidate.candidate_type for candidate in result.candidates)
        cross_optional = dict(envelope.optional)
        assert dict(own_envelope.optional)["event"]["status"] == "AVAILABLE"
        assert "MONITOR_EVENT_RISK" in own_types and "REVIEW_SAFETY_STOCK" in own_types
        assert cross_optional["event"]["status"] == "ABSENT"
        assert cross_optional["simulation"]["status"] == "ABSENT"
        assert "MONITOR_EVENT_RISK" not in cross_types and "REVIEW_SAFETY_STOCK" not in cross_types
        repeat_envelope, repeat_result, _ = _resolve(ids, "consumption")
        assert repeat_envelope == envelope and repeat_result == result
        _assert_read_only(ids, before)
        print("CONTEXT D3-A PASS", {
            "fixture_setup_ms": round((setup_end - started) * 1000, 3),
            "resolver_ms": round(timings[0] * 1000, 3), "policy_ms": round(timings[1] * 1000, 3),
            "combined_ms": round(timings[2] * 1000, 3), "read_only": True,
        }, flush=True)
    finally:
        cleanup = perf_counter()
        d2._cleanup([roots.pop()], [])
        print("CONTEXT D3-A CLEANUP PASS", {"cleanup_ms": round((perf_counter() - cleanup) * 1000, 3), "residue": 0}, flush=True)


def consumption_to_sales():
    started = perf_counter()
    # build supplies only the sales required evidence; consumption owns the Event.
    ids = build("context_demand_consumption_to_sales")
    session = SessionLocal()
    try:
        d2._forecast(session, ids, "SKU", "consumption", T1, "finished_good")
        d2._runtime(session, ids, "SKU", "consumption", T1, "safety_stock")
        session.add(d2._event(ids, "EVENT-CONSUMPTION", T1, "POSITIVE_ASSOCIATION", "SKU", "consumption"))
        session.commit()
        persisted_event = session.query(EventIntelligenceMemory).filter_by(
            company_id=ids["company_id"], material_code="SKU", demand_type="consumption"
        ).one()
        before = _counts(session, ids["company_id"])
    finally:
        session.close()
    setup_end = perf_counter()
    try:
        own_envelope, own_result, _ = _resolve(ids, "consumption")
        envelope, result, timings = _resolve(ids, "sales")
        print("CONTEXT D3-B DIAGNOSTIC", {
            "consumption_control": _identity(own_envelope, own_result, "consumption", "consumption"),
            "sales_cross_scope": _identity(envelope, result, "sales", "consumption"),
            "persisted_event_id": str(persisted_event.id),
        }, flush=True)
        own_types = tuple(candidate.candidate_type for candidate in own_result.candidates)
        cross_types = tuple(candidate.candidate_type for candidate in result.candidates)
        assert dict(own_envelope.optional)["event"]["status"] == "AVAILABLE"
        assert "MONITOR_EVENT_RISK" in own_types
        assert dict(envelope.optional)["event"]["status"] == "ABSENT"
        assert "MONITOR_EVENT_RISK" not in cross_types
        repeat_envelope, repeat_result, _ = _resolve(ids, "sales")
        assert repeat_envelope == envelope and repeat_result == result
        _assert_read_only(ids, before)
        print("CONTEXT D3-B PASS", {
            "fixture_setup_ms": round((setup_end - started) * 1000, 3),
            "resolver_ms": round(timings[0] * 1000, 3), "policy_ms": round(timings[1] * 1000, 3),
            "combined_ms": round(timings[2] * 1000, 3), "read_only": True,
        }, flush=True)
    finally:
        cleanup = perf_counter()
        d2._cleanup([roots.pop()], [])
        print("CONTEXT D3-B CLEANUP PASS", {"cleanup_ms": round((perf_counter() - cleanup) * 1000, 3), "residue": 0}, flush=True)


if __name__ == "__main__":
    sales_to_consumption()
    consumption_to_sales()
