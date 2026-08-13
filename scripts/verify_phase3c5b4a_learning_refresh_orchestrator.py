"""Focused PostgreSQL proof for callable Learning Evidence refresh routing."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost
from sqlalchemy.exc import IntegrityError

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.champion_rollback import ChampionRollbackService
from app.application.company_learning_materialization import CompanyLearningMaterializationService
from app.application.company_learning_refresh import CompanyLearningRefreshService
from app.application.learning_evidence import LearningEvidenceService
from app.application.learning_refresh_orchestrator import (
    LearningEvidenceNotFound, LearningEvidenceTenantViolation, LearningRefreshOrchestrator,
    LearningRefreshRoutingError,
)
from app.application.pattern_learning_materialization import PatternLearningMaterializationService
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.model_artifact import ModelArtifact
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape
from scripts.support.rollback_xgboost_fixture import create as create_rollback_fixture, cleanup as cleanup_rollback_fixture


def _projection_signature(company_id):
    session = SessionLocal()
    try:
        company = session.query(CompanyLearningMemoryV2).filter_by(company_id=company_id).one_or_none()
        patterns = tuple((row.material_code, row.demand_type, row.row_version, row.source_pattern_fingerprint)
                         for row in session.query(PatternLearningMemory).filter_by(company_id=company_id)
                         .order_by(PatternLearningMemory.material_code, PatternLearningMemory.demand_type))
        return (None if company is None else (company.id, company.row_version, company.source_summary_fingerprint,
                                               company.evidence_maturity_score), patterns)
    finally:
        session.close()


def _non_projection_counts(company_id):
    session = SessionLocal()
    try:
        return (
            session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
            session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
            session.query(ForecastVintage).filter_by(company_id=company_id).count(),
            session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
            session.query(RuntimeExecution).filter_by(company_id=company_id).count(),
            session.query(RuntimeTask).filter_by(company_id=company_id).count(),
            session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
            session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
            session.query(RetrainingJob).filter_by(company_id=company_id).count(),
            session.query(ModelArtifact).filter_by(company_id=company_id).count(),
            session.query(ChampionRegistryEntry).filter_by(company_id=company_id).count(),
            session.query(ChampionRegistryCurrent).filter_by(company_id=company_id).count(),
            session.query(ChampionRegistryTransition).filter_by(company_id=company_id).count(),
        )
    finally:
        session.close()


def _observation_id(root, material_code, demand_type, period):
    session = SessionLocal()
    try:
        return session.query(ActualWeeklyObservation).filter_by(company_id=root["company_id"], material_code=material_code,
            demand_type=demand_type, period=period).one().id
    finally:
        session.close()


def _correction(root, material_code, demand_type, period, quantity, accepted):
    proposed = ActualWeeklyLedgerService().ingest_dataset_actuals(root["company_id"], root["user_id"], root["dataset_id"], [{
        "material_code": material_code, "period": period, "quantity": quantity,
        "product_level": "finished_good", "product_group": "G", "product_class": "C",
    }], demand_type)
    revision_id = proposed["revision_ids"][0]
    (ActualWeeklyLedgerService().approve_revision if accepted else ActualWeeklyLedgerService().reject_revision)(
        root["company_id"], revision_id, root["user_id"],
    )
    return revision_id


def _terminal_job(root):
    session = SessionLocal()
    try:
        eligibility = next(row for row in RetrainingEligibilityService(session).evaluate(
            root["company_id"], root["demand_type"], root["start_period"], root["end_period"],
        ) if row.material_code == root["material_code"])
    finally:
        session.close()
    accepted = RetrainingJobService().accept_candidate(RetrainingJobRequest(
        root["company_id"], root["material_code"], root["demand_type"], root["start_period"],
        root["end_period"], "2026-W24", eligibility,
    ))
    assert accepted.status == "CREATED"
    session = SessionLocal()
    try:
        job = session.query(RetrainingJob).filter_by(id=accepted.job_id, company_id=root["company_id"]).one()
        job.state = "not_trainable"; job.completed_at = datetime.now(timezone.utc)
        session.commit()
        return job.id
    finally:
        session.close()


def _clear_tier(root):
    session = SessionLocal()
    try:
        session.query(CompanyLearningMemoryV2).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        session.query(PatternLearningMemory).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        session.query(LearningRefreshDelivery).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        for evidence in session.query(LearningEvidence).filter_by(company_id=root["company_id"]).order_by(
                LearningEvidence.recorded_at.desc(), LearningEvidence.id.desc()).all():
            session.delete(evidence); session.flush()
        session.query(RetrainingJob).filter_by(company_id=root["company_id"]).delete(synchronize_session=False)
        session.commit()
        cleanup_fixture(session, type("FixtureIds", (), root)())
    finally:
        session.close()


def _invalid_evidence_is_rejected(root):
    """The DB check makes unsupported event types impossible to route."""
    session = SessionLocal()
    try:
        actual = session.query(ActualWeeklyObservation).filter_by(company_id=root["company_id"]).first()
        session.add(LearningEvidence(
            company_id=root["company_id"], event_type="UNSUPPORTED", material_code=actual.material_code,
            demand_type=actual.demand_type, source_entity_type="actual_weekly_observation", source_entity_id=actual.id,
            source_revision_identity="invalid", affected_start_period=actual.period, affected_end_period=actual.period,
            evidence_fingerprint="f" * 64, contract_version="test", payload_version="test", evidence_payload={},
            occurred_at=datetime.now(timezone.utc),
        ))
        try:
            session.commit()
            raise AssertionError("unsupported LearningEvidence was persisted")
        except IntegrityError:
            session.rollback()
    finally:
        session.close()


def _malformed_scope_is_rejected(root):
    """A syntactically valid row still cannot route when its source scope disagrees."""
    session = SessionLocal()
    try:
        actual = session.query(ActualWeeklyObservation).filter_by(company_id=root["company_id"]).first()
        malformed = LearningEvidence(
            company_id=root["company_id"], event_type="ACTUAL_ACCEPTED", material_code="SCOPE_MISMATCH",
            demand_type=actual.demand_type, source_entity_type="actual_weekly_observation", source_entity_id=actual.id,
            source_revision_identity="test-scope-mismatch", affected_start_period=actual.period,
            affected_end_period=actual.period, evidence_fingerprint="e" * 64, contract_version="test",
            payload_version="test", evidence_payload={}, occurred_at=datetime.now(timezone.utc),
        )
        session.add(malformed); session.commit()
        try:
            LearningRefreshOrchestrator().orchestrate(root["company_id"], malformed.id)
            raise AssertionError("scope-mismatched evidence was routed")
        except LearningRefreshRoutingError as exc:
            assert str(exc) == "LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH"
        session.delete(malformed); session.commit()
    finally:
        session.close()


async def main():
    roots = []
    rollback_ids = rollback_refs = None
    original_fit = xgboost.XGBRegressor.fit
    fit_calls = {"count": 0}
    try:
        root = await create_tier_shape("tier3", 8, "SKU", "sales")
        roots.append(root)
        other = await create_tier_shape("tier3", 8, "SKU", "sales")
        roots.append(other)
        evidence_service = LearningEvidenceService()
        pattern_materializer = PatternLearningMaterializationService()
        # B is deliberately materialized before A routing and must never be touched by A evidence.
        assert pattern_materializer.materialize(other["company_id"], other["material_code"], other["demand_type"], other["end_period"]).status == "CREATED"
        assert CompanyLearningMaterializationService().materialize(other["company_id"]).status == "CREATED"
        other_before = _projection_signature(other["company_id"])

        ordering = {"pattern_complete_before_company": False}
        def _assert_pattern_first(route):
            memory = PatternLearningMaterializationService().get_current(route.company_id, route.material_code, route.demand_type)
            assert memory is not None and memory.cutoff_period == route.pattern_cutoff_period
            ordering["pattern_complete_before_company"] = True
        ordered = LearningRefreshOrchestrator(before_company_refresh=_assert_pattern_first)
        actual = evidence_service.record_actual_accepted(root["company_id"], _observation_id(root, "SKU", "sales", "2026-W28"))
        actual_before = _non_projection_counts(root["company_id"])
        actual_result = ordered.orchestrate(root["company_id"], actual.evidence_id)
        assert (actual_result.outcome, actual_result.pattern_status, actual_result.company_status) == ("COMPLETED", "CREATED", "CREATED")
        assert ordering["pattern_complete_before_company"] and _non_projection_counts(root["company_id"]) == actual_before
        duplicate = LearningRefreshOrchestrator().orchestrate(root["company_id"], actual.evidence_id)
        assert (duplicate.pattern_status, duplicate.company_status) == ("UNCHANGED", "UNCHANGED")
        assert _projection_signature(other["company_id"]) == other_before

        # Accepted corrections are canonical events; rejected corrections have no delivery item at all.
        revision = _correction(root, "SKU", "sales", "2026-W28", 111, True)
        corrected = evidence_service.record_actual_corrected(root["company_id"], revision)
        corrected_result = LearningRefreshOrchestrator().orchestrate(root["company_id"], corrected.evidence_id)
        assert (corrected_result.pattern_status, corrected_result.company_status) == ("UPDATED", "UPDATED")
        rejected_revision = _correction(root, "SKU", "sales", "2026-W28", 112, False)
        before_rejected = _projection_signature(root["company_id"])
        try:
            evidence_service.record_actual_corrected(root["company_id"], rejected_revision)
            raise AssertionError("rejected correction became canonical LearningEvidence")
        except ValueError as exc:
            assert str(exc) == "ACCEPTED_ACTUAL_CORRECTION_REQUIRED"
        assert _projection_signature(root["company_id"]) == before_rejected

        # Forecast evidence is company-only: Pattern source/version cannot move.
        forecast = evidence_service.record_forecast_evaluated(root["company_id"], root["evaluation_id"])
        pattern_before_forecast = _projection_signature(root["company_id"])[1]
        forecast_result = LearningRefreshOrchestrator().orchestrate(root["company_id"], forecast.evidence_id)
        assert (forecast_result.pattern_status, forecast_result.company_status) == (None, "UPDATED")
        assert _projection_signature(root["company_id"])[1] == pattern_before_forecast

        # Terminal Retraining evidence is company-only and has no governance side effect.
        job_id = _terminal_job(root)
        retraining = evidence_service.record_retraining_completed(root["company_id"], job_id)
        retraining_result = LearningRefreshOrchestrator().orchestrate(root["company_id"], retraining.evidence_id)
        assert (retraining_result.pattern_status, retraining_result.company_status) == (None, "UPDATED")

        # Newer canonical source wins; a delayed older evidence delivery cannot roll it back.
        old_revision = _correction(root, "SKU", "sales", "2026-W29", 121, True)
        delayed = evidence_service.record_actual_corrected(root["company_id"], old_revision)
        new_revision = _correction(root, "SKU", "sales", "2026-W30", 141, True)
        newer = evidence_service.record_actual_corrected(root["company_id"], new_revision)
        newer_result = LearningRefreshOrchestrator().orchestrate(root["company_id"], newer.evidence_id)
        delayed_result = LearningRefreshOrchestrator().orchestrate(root["company_id"], delayed.evidence_id)
        assert newer_result.outcome == delayed_result.outcome == "COMPLETED"
        assert (delayed_result.pattern_status, delayed_result.company_status) == ("UNCHANGED", "UNCHANGED")

        # Pattern write commits first. Company failure is retryable from the same immutable evidence.
        partial_revision = _correction(root, "SKU", "sales", "2026-W27", 131, True)
        partial = evidence_service.record_actual_corrected(root["company_id"], partial_revision)
        failed_after_pattern = LearningRefreshOrchestrator(
            before_company_refresh=lambda _: (_ for _ in ()).throw(RuntimeError("INJECTED_COMPANY_FAILURE")),
        ).orchestrate(root["company_id"], partial.evidence_id)
        assert (failed_after_pattern.outcome, failed_after_pattern.pattern_status, failed_after_pattern.failure_stage) == (
            "FAILED", "UPDATED", "BEFORE_COMPANY_REFRESH")
        partial_retry = LearningRefreshOrchestrator().orchestrate(root["company_id"], partial.evidence_id)
        assert (partial_retry.pattern_status, partial_retry.company_status) == ("UNCHANGED", "UPDATED")

        # Before-pattern failure leaves both projections untouched; a fresh graph can finish it.
        ledger = ActualWeeklyLedgerService()
        rows = [{"material_code": "ISOLATED", "period": f"2026-W{week:02d}", "quantity": 90,
                 "product_level": "finished_good", "product_group": "G", "product_class": "C"} for week in range(1, 33)]
        ledger.ingest_dataset_actuals(root["company_id"], root["user_id"], root["dataset_id"], rows, "sales")
        isolated = evidence_service.record_actual_accepted(root["company_id"], _observation_id(root, "ISOLATED", "sales", "2026-W32"))
        before_pre_failure = _projection_signature(root["company_id"])
        pre_failure = LearningRefreshOrchestrator(
            before_pattern_refresh=lambda _: (_ for _ in ()).throw(RuntimeError("INJECTED_PATTERN_FAILURE")),
        ).orchestrate(root["company_id"], isolated.evidence_id)
        assert pre_failure.outcome == "FAILED" and pre_failure.failure_stage == "BEFORE_PATTERN_REFRESH"
        assert _projection_signature(root["company_id"]) == before_pre_failure
        fresh_retry = LearningRefreshOrchestrator().orchestrate(root["company_id"], isolated.evidence_id)
        assert (fresh_retry.pattern_status, fresh_retry.company_status) == ("CREATED", "UPDATED")

        # Exact material/demand isolation: consumption evidence owns only its consumption Pattern scope.
        patterns_before_consumption = _projection_signature(root["company_id"])[1]
        ledger.ingest_dataset_actuals(root["company_id"], root["user_id"], root["dataset_id"], [{
            "material_code": "SKU", "period": f"2026-W{week:02d}", "quantity": 75 if week == 32 else 70,
            "product_level": "finished_good", "product_group": "G", "product_class": "C",
        } for week in range(1, 33)], "consumption")
        consumption_event = evidence_service.record_actual_accepted(
            root["company_id"], _observation_id(root, "SKU", "consumption", "2026-W32"),
        )
        consumption_result = LearningRefreshOrchestrator().orchestrate(root["company_id"], consumption_event.evidence_id)
        assert (consumption_result.pattern_status, consumption_result.company_status) == ("CREATED", "UPDATED")
        session = SessionLocal()
        try:
            scoped = {(row.material_code, row.demand_type): (row.row_version, row.source_pattern_fingerprint)
                      for row in session.query(PatternLearningMemory).filter_by(company_id=root["company_id"])}
            before_scoped = {(material, demand): (version, fingerprint)
                             for material, demand, version, fingerprint in patterns_before_consumption}
            assert scoped[("SKU", "consumption")][0] == 1
            assert scoped[("SKU", "sales")] == before_scoped[("SKU", "sales")]
            assert scoped[("ISOLATED", "sales")] == before_scoped[("ISOLATED", "sales")]
        finally:
            session.close()
        assert _projection_signature(other["company_id"]) == other_before

        # Governance events from a separate durable fixture are routed only to Company Learning.
        rollback_ids, rollback_refs = create_rollback_fixture()
        session = SessionLocal()
        try:
            promotion_id = session.query(ChampionRegistryTransition).filter_by(
                company_id=rollback_ids.company_id, transition_type="PROMOTION").first().id
        finally:
            session.close()
        promoted = evidence_service.record_champion_promotion(rollback_ids.company_id, promotion_id)
        promote_before = _non_projection_counts(rollback_ids.company_id)
        promoted_result = LearningRefreshOrchestrator().orchestrate(rollback_ids.company_id, promoted.evidence_id)
        assert (promoted_result.pattern_status, promoted_result.company_status) == (None, "CREATED")
        assert _non_projection_counts(rollback_ids.company_id) == promote_before
        rollback = ChampionRollbackService().rollback(rollback_ids.company_id, rollback_ids.material_code, rollback_ids.demand_type,
            rollback_ids.entry_c_id, rollback_ids.entry_b_id, "orchestration source")
        assert rollback.status == "ROLLED_BACK"
        rolled_back = evidence_service.record_champion_rollback(rollback_ids.company_id, rollback.transition_id)
        rollback_result = LearningRefreshOrchestrator().orchestrate(rollback_ids.company_id, rolled_back.evidence_id)
        assert (rollback_result.pattern_status, rollback_result.company_status) == (None, "UPDATED")
        # Failure and retry for company-only evidence cannot create a Pattern projection.
        company_only_failure = LearningRefreshOrchestrator(
            before_company_refresh=lambda _: (_ for _ in ()).throw(RuntimeError("INJECTED_COMPANY_ONLY_FAILURE")),
        ).orchestrate(rollback_ids.company_id, rolled_back.evidence_id)
        assert company_only_failure.outcome == "FAILED" and company_only_failure.pattern_status is None
        session = SessionLocal()
        try:
            assert session.query(PatternLearningMemory).filter_by(company_id=rollback_ids.company_id).count() == 0
        finally:
            session.close()
        # A fresh company-only transition confirms a failed delivery retries the Company row only.
        second_rollback = ChampionRollbackService().rollback(
            rollback_ids.company_id, rollback_ids.material_code, rollback_ids.demand_type,
            rollback_ids.entry_b_id, rollback_ids.entry_a_id, "company-only retry source",
        )
        assert second_rollback.status == "ROLLED_BACK"
        company_retry_event = evidence_service.record_champion_rollback(rollback_ids.company_id, second_rollback.transition_id)
        failed_company_only = LearningRefreshOrchestrator(
            before_company_refresh=lambda _: (_ for _ in ()).throw(RuntimeError("INJECTED_COMPANY_ONLY_FAILURE")),
        ).orchestrate(rollback_ids.company_id, company_retry_event.evidence_id)
        assert failed_company_only.outcome == "FAILED" and failed_company_only.pattern_status is None
        company_only_retry = LearningRefreshOrchestrator().orchestrate(rollback_ids.company_id, company_retry_event.evidence_id)
        assert (company_only_retry.pattern_status, company_only_retry.company_status) == (None, "UPDATED")

        # Tenant, unknown-source, malformed-scope, and database-enforced unsupported-event rejection.
        try:
            LearningRefreshOrchestrator().orchestrate(other["company_id"], actual.evidence_id)
            raise AssertionError("cross-tenant evidence was routed")
        except LearningEvidenceTenantViolation:
            pass
        try:
            LearningRefreshOrchestrator().orchestrate(root["company_id"], UUID("00000000-0000-0000-0000-000000000000"))
            raise AssertionError("unknown evidence was routed")
        except LearningEvidenceNotFound:
            pass
        _invalid_evidence_is_rejected(root)
        _malformed_scope_is_rejected(root)

        # No orchestrated action invokes fitting or downstream analysis.
        xgboost.XGBRegressor.fit = lambda *args, **kwargs: (fit_calls.__setitem__("count", fit_calls["count"] + 1), original_fit(*args, **kwargs))[1]
        side_before = _non_projection_counts(root["company_id"])
        final_duplicate = LearningRefreshOrchestrator().orchestrate(root["company_id"], isolated.evidence_id)
        assert (final_duplicate.pattern_status, final_duplicate.company_status) == ("UNCHANGED", "UNCHANGED")
        assert _non_projection_counts(root["company_id"]) == side_before and fit_calls["count"] == 0
        print("PHASE 3C5B4A PROBE PASS", {
            "actual": (actual_result.pattern_status, actual_result.company_status),
            "forecast": forecast_result.company_status, "retraining": retraining_result.company_status,
            "promotion": promoted_result.company_status, "rollback": rollback_result.company_status,
            "duplicate": duplicate.company_status, "out_of_order": delayed_result.company_status,
            "partial_retry": partial_retry.company_status, "xgboost_fit_calls": fit_calls["count"],
        }, flush=True)
    finally:
        xgboost.XGBRegressor.fit = original_fit
        if rollback_ids:
            # LearningEvidence and Company projection depend on the rollback fixture first.
            session = SessionLocal()
            try:
                session.query(CompanyLearningMemoryV2).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False)
                session.query(LearningRefreshDelivery).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False)
                session.query(LearningEvidence).filter_by(company_id=rollback_ids.company_id).delete(synchronize_session=False)
                session.commit()
            finally:
                session.close()
            cleanup_rollback_fixture(rollback_ids, rollback_refs)
        for root in reversed(roots):
            _clear_tier(root)
        session = SessionLocal()
        try:
            assert all(session.query(Company).filter_by(id=root["company_id"]).count() == 0 for root in roots)
        finally:
            session.close()


if __name__ == "__main__":
    asyncio.run(main())
