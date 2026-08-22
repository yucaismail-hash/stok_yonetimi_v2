"""Persisted cutoff-safety proof for the mutable Event current projection."""
from pathlib import Path
import sys
from time import perf_counter

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
    """All tables the resolver/policy must leave untouched in this fixture."""
    names = (
        ("event_observations", EventObservation),
        ("event_revisions", EventRevision),
        ("event_memory", EventIntelligenceMemory),
        ("learning_evidence", LearningEvidence),
        ("learning_delivery", LearningRefreshDelivery),
    )
    result = {
        name: session.query(model).filter_by(company_id=company_id).count()
        for name, model in names
    }
    result["d2_owned_tables"] = d2._read_only_counts(session, company_id)
    return result


def main():
    total = perf_counter()
    ids = build("context_future_event")
    setup_end = perf_counter()
    future_cutoff = "2026-W24"
    session = SessionLocal()
    try:
        # There is deliberately no compatible historical Event projection.
        future = d2._event(
            ids, "EVENT-FUTURE", future_cutoff, "POSITIVE_ASSOCIATION", "SKU", "sales"
        )
        session.add(future)
        session.commit()
        future_id = str(future.id)
        before = _counts(session, ids["company_id"])
    finally:
        session.close()

    try:
        resolver = DecisionEvidenceResolver()
        resolver_start = perf_counter()
        envelope = resolver.resolve(ids["company_id"], "SKU", "sales", T1, "REPLENISHMENT")
        resolver_end = perf_counter()
        policy = DecisionPolicy()
        result = policy.evaluate(envelope)
        policy_end = perf_counter()
        event = dict(envelope.optional)["event"]
        print(
            "CONTEXT FUTURE EVENT DIAGNOSTIC",
            {
                "envelope_status": envelope.status,
                "material": envelope.material_code,
                "demand_type": envelope.demand_type,
                "decision_cutoff": envelope.decision_cutoff_period,
                "event": {
                    "status": event["status"],
                    "reason": event.get("reason"),
                    "memory_id": future_id,
                    "event_identity": "EVENT-FUTURE",
                    "classification": "POSITIVE_ASSOCIATION",
                    "cutoff_period": future_cutoff,
                },
                "candidate_types": tuple(candidate.candidate_type for candidate in result.candidates),
                "support": result.supporting_evidence,
                "confidence": result.confidence,
            },
            flush=True,
        )
        assert event["status"] == "INCOMPATIBLE" and event["reason"] == "FUTURE_EVIDENCE"
        assert all(candidate.candidate_type != "MONITOR_EVENT_RISK" for candidate in result.candidates)
        assert "EVENT_ASSOCIATION_NON_CAUSAL" not in result.supporting_evidence
        assert all("EVENT_ASSOCIATION" not in code for code in result.supporting_evidence)

        repeat_envelope = resolver.resolve(ids["company_id"], "SKU", "sales", T1, "REPLENISHMENT")
        repeat_result = policy.evaluate(repeat_envelope)
        assert repeat_envelope == envelope and repeat_result == result

        session = SessionLocal()
        try:
            after = _counts(session, ids["company_id"])
        finally:
            session.close()
        assert after == before, {"before": before, "after": after}
        print(
            "CONTEXT FUTURE EVENT PASS",
            {
                "fixture_setup_ms": round((setup_end - total) * 1000, 3),
                "resolver_ms": round((resolver_end - resolver_start) * 1000, 3),
                "policy_ms": round((policy_end - resolver_end) * 1000, 3),
                "combined_ms": round((policy_end - resolver_start) * 1000, 3),
                "read_only": True,
            },
            flush=True,
        )
    finally:
        cleanup_start = perf_counter()
        d2._cleanup([roots.pop()], [])
        print(
            "CONTEXT FUTURE EVENT CLEANUP PASS",
            {"cleanup_ms": round((perf_counter() - cleanup_start) * 1000, 3), "residue": 0},
            flush=True,
        )


if __name__ == "__main__":
    main()
