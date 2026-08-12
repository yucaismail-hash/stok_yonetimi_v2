"""Focused PostgreSQL proof for immutable, source-derived Learning Evidence."""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.learning_evidence import LearningEvidenceService, canonical_evidence_fingerprint
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.application.champion_rollback import ChampionRollbackService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.learning_evidence import LearningEvidence
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape
from scripts.support.rollback_xgboost_fixture import create as create_rollback_fixture, cleanup as cleanup_rollback_fixture


def _counts(company_id):
    session = SessionLocal()
    try:
        return {
            "actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
            "revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
            "vintages": session.query(ForecastVintage).filter_by(company_id=company_id).count(),
            "evaluations": session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
            "runtime_executions": session.query(RuntimeExecution).filter_by(company_id=company_id).count(),
            "runtime_tasks": session.query(RuntimeTask).filter_by(company_id=company_id).count(),
            "runtime_attempts": session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
            "runtime_results": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
            "artifacts": session.query(ModelArtifact).filter_by(company_id=company_id).count(),
            "registry_entries": session.query(ChampionRegistryEntry).filter_by(company_id=company_id).count(),
            "registry_current": session.query(ChampionRegistryCurrent).filter_by(company_id=company_id).count(),
            "registry_transitions": session.query(ChampionRegistryTransition).filter_by(company_id=company_id).count(),
            "jobs": session.query(RetrainingJob).filter_by(company_id=company_id).count(),
            "company_learning": session.query(CompanyLearningMemory).filter_by(company_id=company_id).count(),
            "user_learning": session.query(UserLearningData).filter_by(company_id=company_id).count(),
        }
    finally:
        session.close()


def _observation(company_id, material_code, demand_type, period):
    session = SessionLocal()
    try:
        return session.query(ActualWeeklyObservation).filter_by(company_id=company_id, material_code=material_code, demand_type=demand_type, period=period).one().id
    finally:
        session.close()


def _eligibility(fixture):
    session = SessionLocal()
    try:
        rows = RetrainingEligibilityService(session).evaluate(fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"])
        return next(row for row in rows if row.material_code == fixture["material_code"])
    finally:
        session.close()


def _accept_correction(fixture, quantity, approve):
    ledger = ActualWeeklyLedgerService()
    proposed = ledger.ingest_dataset_actuals(fixture["company_id"], fixture["user_id"], fixture["dataset_id"], [{
        "material_code": fixture["material_code"], "period": fixture["end_period"], "quantity": quantity,
        "product_level": fixture["product_level"], "product_group": "G", "product_class": "C",
    }], fixture["demand_type"])
    revision_id = proposed["revision_ids"][0]
    (ledger.approve_revision if approve else ledger.reject_revision)(fixture["company_id"], revision_id, fixture["user_id"])
    return revision_id


def _cleanup_root(root):
    session = SessionLocal()
    try:
        # Remove dependent immutable evidence first, newest superseding rows first.
        for evidence in session.query(LearningEvidence).filter_by(company_id=root["company_id"]).order_by(LearningEvidence.recorded_at.desc(), LearningEvidence.id.desc()).all():
            session.delete(evidence)
            # SQLAlchemy may otherwise batch parent and child self-FK deletes.
            session.flush()
        session.query(RetrainingJob).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        session.commit()
        cleanup_fixture(session, type("FixtureIds", (), root)())
    finally:
        session.close()


def _cleanup_rollback(ids, refs):
    session = SessionLocal()
    try:
        for evidence in session.query(LearningEvidence).filter_by(company_id=ids.company_id).order_by(LearningEvidence.recorded_at.desc(), LearningEvidence.id.desc()).all():
            session.delete(evidence)
            session.flush()
        session.commit()
    finally:
        session.close()
    cleanup_rollback_fixture(ids, refs)


async def main():
    roots = []
    rollback_ids = rollback_refs = None
    original_fit = xgboost.XGBRegressor.fit
    fit_calls = {"count": 0}
    xgboost.XGBRegressor.fit = lambda *args, **kwargs: (fit_calls.__setitem__("count", fit_calls["count"] + 1), original_fit(*args, **kwargs))[1]
    try:
        root = await create_tier_shape("tier3", 8, "MATERIAL_A", "sales")
        roots.append(root)
        shared = {name: root[name] for name in ("company_id", "user_id", "dataset_id")}
        material_b = await create_tier_shape("tier3", 8, "MATERIAL_B", "sales", context=shared)
        consumption = await create_tier_shape("tier3", 8, "MATERIAL_A", "consumption", context=shared)
        other_company = await create_tier_shape("tier3", 8, "MATERIAL_A", "sales")
        roots.append(other_company)
        service = LearningEvidenceService()

        initial_id = _observation(root["company_id"], root["material_code"], root["demand_type"], root["end_period"])
        before = _counts(root["company_id"])
        first = service.record_actual_accepted(root["company_id"], initial_id)
        duplicate = service.record_actual_accepted(root["company_id"], initial_id)
        assert (first.status, duplicate.status, first.evidence_id, duplicate.evidence_id) == ("CREATED", "ALREADY_EXISTS", first.evidence_id, first.evidence_id)
        assert _counts(root["company_id"]) == before

        race_id = _observation(root["company_id"], material_b["material_code"], material_b["demand_type"], material_b["end_period"])
        barrier = threading.Barrier(2)
        def contender():
            barrier.wait()
            return LearningEvidenceService().record_actual_accepted(root["company_id"], race_id)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: contender(), range(2)))
        assert sorted(item.status for item in outcomes) == ["ALREADY_EXISTS", "CREATED"]
        session = SessionLocal()
        try:
            assert session.query(LearningEvidence).filter_by(company_id=root["company_id"], evidence_fingerprint=outcomes[0].evidence_fingerprint).count() == 1
        finally:
            session.close()

        correction_id = _accept_correction(root, 220, True)
        corrected = service.record_actual_corrected(root["company_id"], correction_id)
        session = SessionLocal()
        try:
            correction = session.query(LearningEvidence).filter_by(id=corrected.evidence_id, company_id=root["company_id"]).one()
            original = session.query(LearningEvidence).filter_by(id=first.evidence_id, company_id=root["company_id"]).one()
            assert corrected.status == "CREATED" and correction.supersedes_evidence_id == original.id and correction.evidence_fingerprint != original.evidence_fingerprint
            assert [row.id for row in service.lineage(root["company_id"], correction.id)] == [correction.id, original.id]
        finally:
            session.close()
        rejected_id = _accept_correction(root, 230, False)
        evidence_count = len(service.list_scope(root["company_id"]))
        try:
            service.record_actual_corrected(root["company_id"], rejected_id)
            raise AssertionError("rejected correction was accepted as Learning Evidence")
        except ValueError as exc:
            assert str(exc) == "ACCEPTED_ACTUAL_CORRECTION_REQUIRED"
        assert len(service.list_scope(root["company_id"])) == evidence_count

        evaluation = service.record_forecast_evaluated(root["company_id"], root["evaluation_id"])
        assert evaluation.status == "CREATED"
        # Create a terminal canonical job through B1, then persist its terminal source state for this evidence-only probe.
        accepted = RetrainingJobService().accept_candidate(RetrainingJobRequest(root["company_id"], root["material_code"], root["demand_type"], root["start_period"], root["end_period"], "2026-W24", _eligibility(root)))
        assert accepted.status == "CREATED"
        session = SessionLocal()
        try:
            job = session.query(RetrainingJob).filter_by(id=accepted.job_id, company_id=root["company_id"]).one()
            job.state = "not_trainable"
            session.commit()
        finally:
            session.close()
        retraining = service.record_retraining_completed(root["company_id"], accepted.job_id)
        assert retraining.status == "CREATED"

        material_event = service.record_actual_accepted(root["company_id"], race_id)
        consumption_id = _observation(root["company_id"], consumption["material_code"], consumption["demand_type"], consumption["end_period"])
        consumption_event = service.record_actual_accepted(root["company_id"], consumption_id)
        other_id = _observation(other_company["company_id"], other_company["material_code"], other_company["demand_type"], other_company["end_period"])
        other_event = service.record_actual_accepted(other_company["company_id"], other_id)
        assert material_event.evidence_id != consumption_event.evidence_id and consumption_event.evidence_id != other_event.evidence_id
        assert service.get(other_company["company_id"], first.evidence_id) is None
        for invalid in (lambda: service.record_actual_accepted(other_company["company_id"], initial_id), lambda: service.record_forecast_evaluated(root["company_id"], "00000000-0000-0000-0000-000000000000")):
            try:
                invalid(); raise AssertionError("invalid source accepted")
            except LookupError:
                pass

        rollback_ids, rollback_refs = create_rollback_fixture()
        session = SessionLocal()
        try:
            promotion = session.query(ChampionRegistryTransition).filter_by(company_id=rollback_ids.company_id, transition_type="PROMOTION").first()
            promotion_id = promotion.id
        finally:
            session.close()
        promoted = service.record_champion_promotion(rollback_ids.company_id, promotion_id)
        rollback = ChampionRollbackService().rollback(rollback_ids.company_id, rollback_ids.material_code, rollback_ids.demand_type, rollback_ids.entry_c_id, rollback_ids.entry_b_id, "learning evidence source")
        assert rollback.status == "ROLLED_BACK"
        rolled_back = service.record_champion_rollback(rollback_ids.company_id, rollback.transition_id)
        assert promoted.status == rolled_back.status == "CREATED"

        # A fresh session reconstructs only persisted primitive identities and payload lineage.
        session = SessionLocal()
        try:
            fresh = session.query(LearningEvidence).filter_by(id=corrected.evidence_id, company_id=root["company_id"]).one()
            assert fresh.event_type == "ACTUAL_CORRECTED" and fresh.source_entity_id == initial_id and fresh.demand_type == "sales"
            assert canonical_evidence_fingerprint({"a": 1, "b": ["x"]}) == canonical_evidence_fingerprint({"b": ["x"], "a": 1})
            try:
                fresh.material_code = "MUTATED"; session.commit(); raise AssertionError("LearningEvidence mutation succeeded")
            except ValueError:
                session.rollback()
        finally:
            session.close()
        assert fit_calls["count"] == 0
        print("PHASE 3C5B1 PROBE PASS", {"root_evidence": len(service.list_scope(root["company_id"])), "other_company_evidence": len(service.list_scope(other_company["company_id"])), "xgboost_fit_calls": fit_calls["count"]})
    finally:
        xgboost.XGBRegressor.fit = original_fit
        if rollback_ids:
            _cleanup_rollback(rollback_ids, rollback_refs)
        for root in reversed(roots):
            _cleanup_root(root)
        session = SessionLocal()
        try:
            for root in roots:
                assert session.query(Company).filter_by(id=root["company_id"]).count() == 0
        finally:
            session.close()


if __name__ == "__main__":
    asyncio.run(main())
