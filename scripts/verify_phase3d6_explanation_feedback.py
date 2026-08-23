"""Focused PostgreSQL proof: frozen Decision explanations and opinion-only feedback."""
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_explanation import DecisionExplanationService
from app.application.decision_feedback import DecisionFeedbackService
from app.application.decision_policy import DecisionPolicy
from app.application.decision_snapshot import DecisionSnapshotService
from app.database import SessionLocal
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.runtime import RuntimeExecution, RuntimeResultReference
from scripts import verify_phase3d2_decision_evidence_matrix as d2
from scripts.verify_phase3d3a_decision_policy_postgres import T1, build, context


def materialize(ids):
    envelope = DecisionEvidenceResolver().resolve(ids["company_id"], "SKU", "sales", T1, "REPLENISHMENT")
    return DecisionSnapshotService().materialize(envelope, DecisionPolicy().evaluate(envelope)).snapshot_id


def cleanup(ids_list):
    session = SessionLocal()
    try:
        company_ids = [ids["company_id"] for ids in ids_list]
        snapshot_ids = [row[0] for row in session.query(DecisionSnapshot.id).filter(DecisionSnapshot.company_id.in_(company_ids)).all()]
        if snapshot_ids:
            session.query(DecisionFeedbackEvent).filter(DecisionFeedbackEvent.decision_snapshot_id.in_(snapshot_ids)).delete(synchronize_session=False)
            session.query(DecisionSnapshotCandidate).filter(DecisionSnapshotCandidate.decision_snapshot_id.in_(snapshot_ids)).delete(synchronize_session=False)
        session.query(DecisionSnapshot).filter(DecisionSnapshot.company_id.in_(company_ids)).delete(synchronize_session=False); session.commit()
    finally: session.close()
    for ids in reversed(ids_list): d2._cleanup([ids], [])


def main():
    started = perf_counter(); created = []
    try:
        multi = build("d6_multi", supplier="LATE_PRONE", event="POSITIVE_ASSOCIATION", backtest="weak_validation", simulation="stockout_risk"); created.append(multi)
        other = context("phase3d6_other"); created.append(other)
        learned_id = multi_id = materialize(multi)
        print("[3D6] snapshots materialized", flush=True)
        explanation, feedback = DecisionExplanationService(), DecisionFeedbackService()
        learned_view = explanation.get(multi["company_id"], learned_id)
        print("[3D6] first/learned explanations reconstructed", flush=True)
        assert any(x["source"] == "pattern" and x["semantic_type"] == "LEARNED_CONTEXT" for x in learned_view.source_provenance)
        assert any(x["source"] == "event" and x["semantic_type"] == "NON_CAUSAL_ASSOCIATION" for x in learned_view.source_provenance)
        assert learned_view.decision["confidence_policy_version"] == "decision_confidence_v1" and "not success probability" in learned_view.decision["confidence_semantics"]
        multi_view = explanation.get(multi["company_id"], multi_id)
        print("[3D6] multi-risk explanation reconstructed", flush=True)
        multi_types = tuple(x["candidate_type"] for x in multi_view.candidates)
        assert multi_types == ("REVIEW_SAFETY_STOCK", "REVIEW_FORECAST", "REVIEW_SUPPLIER", "MONITOR_EVENT_RISK"), multi_types
        assert multi_view.decision["agreement_status"] == "MIXED" and "SIMULATION_SCENARIO_RISK" in multi_view.decision["supporting_evidence"]
        session = SessionLocal()
        try:
            session.query(d2.PatternLearningMemory).filter_by(company_id=multi["company_id"], material_code="SKU", demand_type="sales").update({"pattern_classification": "LUMPY", "cutoff_period": "2026-W24"})
            session.query(d2.EventIntelligenceMemory).filter_by(company_id=multi["company_id"], material_code="SKU", demand_type="sales").update({"classification": "NO_CLEAR_EFFECT", "cutoff_period": "2026-W24"}); session.commit()
            immutable_before = (session.query(DecisionSnapshot).filter_by(id=learned_id).one().decision_policy_fingerprint, session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=learned_id).count(), session.query(RuntimeExecution).filter_by(company_id=multi["company_id"]).count(), session.query(RuntimeResultReference).filter_by(company_id=multi["company_id"]).count())
        finally: session.close()
        assert explanation.get(multi["company_id"], learned_id) == learned_view
        print("[3D6] historical freeze confirmed", flush=True)
        t = perf_counter(); helpful = feedback.record(multi["company_id"], multi["user_id"], learned_id, "HELPFUL", candidate_ordinal=1, comment="Useful", source_metadata={"client": "phase3d6"}); feedback_ms = (perf_counter()-t)*1000
        t = perf_counter(); duplicate = feedback.record(multi["company_id"], multi["user_id"], learned_id, "HELPFUL", candidate_ordinal=1, comment="Useful", source_metadata={"client": "phase3d6"}); duplicate_ms = (perf_counter()-t)*1000
        changed = feedback.record(multi["company_id"], multi["user_id"], learned_id, "NOT_HELPFUL", candidate_ordinal=1, comment="Useful", supersedes_feedback_id=helpful.feedback_id)
        assert helpful.status == "CREATED" and duplicate.status == "ALREADY_EXISTS" and duplicate.feedback_id == helpful.feedback_id and changed.status == "CREATED"
        print("[3D6] feedback idempotency/supersession confirmed", flush=True)
        t = perf_counter(); listing = feedback.list_for_snapshot(multi["company_id"], learned_id); list_ms = (perf_counter()-t)*1000
        assert len(listing["events"]) == 2 and listing["counts"] == {"HELPFUL": 1, "NOT_HELPFUL": 1} and listing["latest_by_user_candidate"][0]["feedback_type"] == "NOT_HELPFUL"
        try: feedback.record(multi["company_id"], multi["user_id"], learned_id, "HELPFUL", candidate_ordinal=999)
        except ValueError: pass
        else: raise AssertionError("invalid candidate accepted")
        assert explanation.get(other["company_id"], learned_id) is None and feedback.list_for_snapshot(other["company_id"], learned_id) is None
        try: feedback.record(other["company_id"], other["user_id"], learned_id, "HELPFUL")
        except ValueError: pass
        else: raise AssertionError("cross-tenant feedback accepted")
        session = SessionLocal()
        try:
            immutable_after = (session.query(DecisionSnapshot).filter_by(id=learned_id).one().decision_policy_fingerprint, session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=learned_id).count(), session.query(RuntimeExecution).filter_by(company_id=multi["company_id"]).count(), session.query(RuntimeResultReference).filter_by(company_id=multi["company_id"]).count())
            assert immutable_before == immutable_after
        finally: session.close()
        assert DecisionExplanationService().get(multi["company_id"], learned_id) == learned_view
        session = SessionLocal()
        try:
            session.query(d2.PatternLearningMemory).filter_by(company_id=multi["company_id"]).delete(synchronize_session=False); session.query(d2.SupplierLearningMemory).filter_by(company_id=multi["company_id"]).delete(synchronize_session=False); session.query(d2.EventIntelligenceMemory).filter_by(company_id=multi["company_id"]).delete(synchronize_session=False); session.query(d2.CompanyLearningMemoryV2).filter_by(company_id=multi["company_id"]).delete(synchronize_session=False)
            refs = [x[0] for x in session.query(RuntimeResultReference.id).filter_by(company_id=multi["company_id"]).filter(RuntimeResultReference.result_type.in_(("backtest", "simulation"))).all()]; session.query(RuntimeResultReference).filter(RuntimeResultReference.id.in_(refs)).delete(synchronize_session=False); session.query(RuntimeExecution).filter_by(company_id=multi["company_id"]).filter(RuntimeExecution.analysis_type.in_(("backtest", "simulation"))).delete(synchronize_session=False); session.commit()
        finally: session.close()
        first_id = materialize(multi); t = perf_counter(); first_view = explanation.get(multi["company_id"], first_id); explanation_ms = (perf_counter()-t)*1000
        assert first_view.decision["status"] == "READY" and first_view.candidates[0]["candidate_type"] == "HOLD_POLICY" and any(x["source"] == "company_learning" and x["evidence"]["status"] == "ABSENT" for x in first_view.source_provenance)
        print("PHASE 3D6 PASS", {"first_use": first_view.candidates[0]["candidate_type"], "learned_candidates": len(learned_view.candidates), "multi_candidates": len(multi_view.candidates), "historical_freeze": True, "feedback_events": len(listing["events"]), "explanation_ms": round(explanation_ms, 3), "feedback_create_ms": round(feedback_ms, 3), "duplicate_lookup_ms": round(duplicate_ms, 3), "feedback_list_ms": round(list_ms, 3), "total_ms": round((perf_counter()-started)*1000, 3)}, flush=True)
    finally:
        cleanup(created); print("PHASE 3D6 CLEANUP PASS", {"residue": 0}, flush=True)


if __name__ == "__main__": main()
