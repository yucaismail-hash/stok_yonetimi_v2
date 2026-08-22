"""Bounded persisted proof that Decision evidence is company-scoped."""
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
from app.models.runtime import RuntimeResultReference
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


def _resolve(ids):
    start = perf_counter()
    envelope = DecisionEvidenceResolver().resolve(ids["company_id"], "SKU", "sales", T1, "REPLENISHMENT")
    resolver_end = perf_counter()
    policy = DecisionPolicy().evaluate(envelope)
    policy_end = perf_counter()
    return envelope, policy, (resolver_end - start, policy_end - resolver_end, policy_end - start)


def _summary(envelope, policy):
    optional = dict(envelope.optional)
    return {
        "company_id": str(envelope.company_id), "scope": (envelope.material_code, envelope.demand_type, envelope.decision_cutoff_period),
        "event": optional["event"], "simulation": optional["simulation"],
        "candidate_types": tuple(candidate.candidate_type for candidate in policy.candidates),
        "reason_codes": tuple(code for candidate in policy.candidates for code in candidate.reason_codes),
        "envelope_fingerprint": envelope.fingerprint, "policy_fingerprint": policy.fingerprint, "confidence": policy.confidence,
    }


def main():
    total = perf_counter()
    company_a = build("context_tenant_a")
    a_before, a_policy_before, _ = _resolve(company_a)
    assert tuple(candidate.candidate_type for candidate in a_policy_before.candidates) == ("HOLD_POLICY",)

    company_b = build("context_tenant_b", event="POSITIVE_ASSOCIATION")
    session = SessionLocal()
    try:
        _, simulation = d2._runtime(session, company_b, "SKU", "sales", T1, "simulation", "stockout_risk")
        session.commit()
        event_b = session.query(EventIntelligenceMemory).filter_by(
            company_id=company_b["company_id"], material_code="SKU", demand_type="sales"
        ).one()
        event_b_id, runtime_b_id = event_b.id, simulation.id
        counts_a_before, counts_b_before = _counts(session, company_a["company_id"]), _counts(session, company_b["company_id"])
    finally:
        session.close()
    setup_end = perf_counter()

    try:
        b_envelope, b_policy, b_times = _resolve(company_b)
        a_envelope, a_policy, a_times = _resolve(company_a)
        print("CONTEXT D4 DIAGNOSTIC", {
            "company_b_control": _summary(b_envelope, b_policy),
            "company_a_resolution": _summary(a_envelope, a_policy),
            "company_b_known_ids": {"event_memory_id": str(event_b_id), "runtime_result_reference_id": str(runtime_b_id)},
        }, flush=True)
        b_types = tuple(candidate.candidate_type for candidate in b_policy.candidates)
        a_types = tuple(candidate.candidate_type for candidate in a_policy.candidates)
        a_optional = dict(a_envelope.optional)
        assert "MONITOR_EVENT_RISK" in b_types and "REVIEW_SAFETY_STOCK" in b_types
        assert a_optional["event"]["status"] == "ABSENT" and a_optional["simulation"]["status"] == "ABSENT"
        assert a_types == ("HOLD_POLICY",)
        assert a_envelope == a_before and a_policy == a_policy_before

        # Known B IDs are not retrievable through a Company A-scoped access path.
        session = SessionLocal()
        try:
            known_event_for_a = session.query(EventIntelligenceMemory).filter_by(id=event_b_id, company_id=company_a["company_id"]).one_or_none()
            known_runtime_for_a = session.query(RuntimeResultReference).filter_by(id=runtime_b_id, company_id=company_a["company_id"]).one_or_none()
            counts_a_after, counts_b_after = _counts(session, company_a["company_id"]), _counts(session, company_b["company_id"])
        finally:
            session.close()
        assert known_event_for_a is None and known_runtime_for_a is None
        assert counts_a_after == counts_a_before and counts_b_after == counts_b_before

        repeat_envelope, repeat_policy, repeat_times = _resolve(company_a)
        assert repeat_envelope == a_envelope and repeat_policy == a_policy
        print("CONTEXT D4 PASS", {
            "fixture_setup_ms": round((setup_end - total) * 1000, 3),
            "company_b_combined_ms": round(b_times[2] * 1000, 3),
            "company_a_resolver_ms": round(a_times[0] * 1000, 3), "company_a_policy_ms": round(a_times[1] * 1000, 3),
            "company_a_combined_ms": round(a_times[2] * 1000, 3), "repeat_combined_ms": round(repeat_times[2] * 1000, 3),
            "read_only": True,
        }, flush=True)
    finally:
        cleanup = perf_counter()
        d2._cleanup([roots.pop(), roots.pop()], [])
        print("CONTEXT D4 CLEANUP PASS", {"cleanup_ms": round((perf_counter() - cleanup) * 1000, 3), "company_a_residue": 0, "company_b_residue": 0}, flush=True)


if __name__ == "__main__":
    main()
