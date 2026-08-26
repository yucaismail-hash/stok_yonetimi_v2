"""Focused PostgreSQL integrity proof for canonical Decision authority and feedback races."""
from pathlib import Path
import sys
from threading import Barrier, Thread

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from app.api.v2 import router as v2_router
from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.application.decision_feedback import DecisionFeedbackService
from app.application.decision_policy import DecisionPolicy
from app.application.decision_snapshot import DecisionSnapshotService
from app.database import SessionLocal
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.model_artifact import ModelArtifact
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference
from app.models.supplier_learning_memory import SupplierLearningMemory
from scripts import verify_phase3d2_decision_evidence_matrix as d2
from scripts.verify_phase3d3a_decision_policy_postgres import T1, build, context


def snapshot(ids):
    envelope = DecisionEvidenceResolver().resolve(ids["company_id"], "SKU", "sales", T1, "REPLENISHMENT")
    return DecisionSnapshotService().materialize(envelope, DecisionPolicy().evaluate(envelope)).snapshot_id


def counts(session, company_id):
    models = (DecisionSnapshot, DecisionSnapshotCandidate, PatternLearningMemory, CompanyLearningMemoryV2, SupplierLearningMemory,
              EventIntelligenceMemory, RuntimeExecution, RuntimeResultReference, RetrainingJob, ModelArtifact, ChampionRegistryEntry, ChampionRegistryCurrent)
    return tuple(session.query(model).filter_by(company_id=company_id).count() if hasattr(model, "company_id") else session.query(model).join(DecisionSnapshot).filter(DecisionSnapshot.company_id == company_id).count() for model in models)


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


def race(call):
    barrier = Barrier(2); outcomes = []
    def worker():
        barrier.wait(); outcomes.append(call())
    threads = [Thread(target=worker), Thread(target=worker)]
    [thread.start() for thread in threads]; [thread.join() for thread in threads]
    return tuple(outcomes)


def route_paths(router):
    paths = []
    for route in router.routes:
        if hasattr(route, "path"):
            paths.append(route.path)
        elif hasattr(route, "router"):
            paths.extend(route_paths(route.router))
    return tuple(paths)


def main():
    ids = build("d7_r2"); other = context("phase3d7_r2_other")
    try:
        snapshot_id = snapshot(ids); service = DecisionFeedbackService()
        session = SessionLocal()
        try:
            before = counts(session, ids["company_id"])
            indexes = session.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'decision_feedback_events' ORDER BY indexname")).all()
            assert any(name == "uq_decision_feedback_company_semantic_key" and "semantic_key" in definition for name, definition in indexes)
        finally: session.close()
        routes = route_paths(v2_router)
        assert not any(path.startswith("/decision") for path in routes), routes
        snapshot_outcomes = race(lambda: service.record(ids["company_id"], ids["user_id"], snapshot_id, "HELPFUL", comment="snapshot"))
        assert sorted(result.status for result in snapshot_outcomes) == ["ALREADY_EXISTS", "CREATED"]
        snapshot_feedback_id = snapshot_outcomes[0].feedback_id
        candidate_outcomes = race(lambda: DecisionFeedbackService().record(ids["company_id"], ids["user_id"], snapshot_id, "HELPFUL", candidate_ordinal=1, comment="candidate"))
        assert sorted(result.status for result in candidate_outcomes) == ["ALREADY_EXISTS", "CREATED"]
        candidate_feedback_id = candidate_outcomes[0].feedback_id
        retry = service.record(ids["company_id"], ids["user_id"], snapshot_id, "HELPFUL", candidate_ordinal=1, comment="candidate")
        assert retry.status == "ALREADY_EXISTS" and retry.feedback_id == candidate_feedback_id
        changed = service.record(ids["company_id"], ids["user_id"], snapshot_id, "NOT_HELPFUL", candidate_ordinal=1, comment="candidate", supersedes_feedback_id=candidate_feedback_id)
        assert changed.status == "CREATED"
        try: service.record(ids["company_id"], ids["user_id"], snapshot_id, "HELPFUL", candidate_ordinal=99)
        except ValueError: pass
        else: raise AssertionError("invalid candidate accepted")
        assert service.list_for_snapshot(other["company_id"], snapshot_id) is None
        for kwargs in ({}, {"supersedes_feedback_id": candidate_feedback_id}):
            try: service.record(other["company_id"], other["user_id"], snapshot_id, "HELPFUL", **kwargs)
            except ValueError: pass
            else: raise AssertionError("cross-tenant feedback accepted")
        session = SessionLocal()
        try:
            events = session.query(DecisionFeedbackEvent).filter_by(company_id=ids["company_id"], decision_snapshot_id=snapshot_id).order_by(DecisionFeedbackEvent.created_at, DecisionFeedbackEvent.id).all()
            assert len(events) == 3 and sum(event.candidate_ordinal is None for event in events) == 1
            assert any(event.id == changed.feedback_id and event.supersedes_feedback_id == candidate_feedback_id for event in events)
            after = counts(session, ids["company_id"])
            assert before == after
            print("PHASE 3D7 R2 PASS", {"routes": routes, "snapshot_race": [result.status for result in snapshot_outcomes], "candidate_race": [result.status for result in candidate_outcomes], "retry": retry.status, "feedback_events": len(events), "index": "uq_decision_feedback_company_semantic_key"}, flush=True)
        finally: session.close()
    finally:
        cleanup([ids, other]); print("PHASE 3D7 R2 CLEANUP PASS", {"residue": 0}, flush=True)


if __name__ == "__main__": main()
