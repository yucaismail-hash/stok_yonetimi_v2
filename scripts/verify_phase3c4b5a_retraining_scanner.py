"""PostgreSQL proof that retraining scanner discovery never starts work."""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.forecast_evaluation_service import ForecastEvaluationService
from app.application.retraining_scanner import RetrainingScannerService
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.retraining_resource_lease import RetrainingResourceLease
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape


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
            "leases": session.query(RetrainingResourceLease).filter_by(company_id=company_id).count(),
            "decisions": session.query(ChampionChallengerDecision).filter_by(company_id=company_id).count(),
            "registry_entries": session.query(ChampionRegistryEntry).filter_by(company_id=company_id).count(),
            "registry_current": session.query(ChampionRegistryCurrent).filter_by(company_id=company_id).count(),
            "registry_transitions": session.query(ChampionRegistryTransition).filter_by(company_id=company_id).count(),
            "company_learning": session.query(CompanyLearningMemory).filter_by(company_id=company_id).count(),
            "user_learning": session.query(UserLearningData).filter_by(company_id=company_id).count(),
        }
    finally:
        session.close()


def _correct(fixture, quantity):
    service = ActualWeeklyLedgerService()
    proposed = service.ingest_dataset_actuals(fixture["company_id"], fixture["user_id"], fixture["dataset_id"], [{
        "material_code": fixture["material_code"], "period": fixture["end_period"], "quantity": quantity,
        "product_level": fixture["product_level"], "product_group": "G", "product_class": "C",
    }], fixture["demand_type"])
    service.approve_revision(fixture["company_id"], proposed["revision_ids"][0], fixture["user_id"])
    session = SessionLocal()
    try:
        ForecastEvaluationService(session).evaluate(fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"])
        session.commit()
    finally:
        session.close()


def _watermark(fixture):
    session = SessionLocal()
    try:
        return next(row.latest_evaluation_id for row in RetrainingEligibilityService(session).evaluate(
            fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"],
        ) if row.material_code == fixture["material_code"])
    finally:
        session.close()


class _ControlledConsumptionFailure:
    """Probe-only one-scope failure: other discovered scopes must continue."""
    def __init__(self, session):
        self._service = RetrainingEligibilityService(session)
    def evaluate(self, company_id, demand_type, start_period, end_period, last_seen_evaluation_id=None):
        if demand_type == "consumption":
            raise ValueError("PROBE_CONSUMPTION_SCOPE_FAILURE")
        return self._service.evaluate(company_id, demand_type, start_period, end_period, last_seen_evaluation_id)


def _cleanup(root):
    session = SessionLocal()
    try:
        company_id = root["company_id"]
        session.query(RetrainingResourceLease).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.query(RetrainingJob).filter_by(company_id=company_id).delete(synchronize_session=False)
        session.commit()
        cleanup_fixture(session, type("FixtureIds", (), root)())
    finally:
        session.close()


async def main():
    roots = []
    original_fit = xgboost.XGBRegressor.fit
    fits = {"count": 0}
    xgboost.XGBRegressor.fit = lambda *args, **kwargs: (fits.__setitem__("count", fits["count"] + 1), original_fit(*args, **kwargs))[1]
    try:
        # One company with genuine Tier 0/1/2/3 persisted evidence scopes.
        stable0 = await create_tier_shape("stable", 4, "T0", "sales"); roots.append(stable0)
        context = {key: stable0[key] for key in ("company_id", "user_id", "dataset_id")}
        stable1 = await create_tier_shape("stable", 4, "T1", "consumption", context=context)
        tier2 = await create_tier_shape("tier2", 8, "T2", "sales", context=context)
        tier3 = await create_tier_shape("tier3", 8, "T3", "sales", context=context)
        scanner = RetrainingScannerService()
        before = _counts(stable0["company_id"])
        mixed = scanner.scan(stable0["company_id"], "2026-W25", "2026-W32", last_seen_evaluation_ids={
            ("T0", "sales"): _watermark(stable0),
        })
        assert (mixed.tier0_count, mixed.tier1_count, mixed.tier2_count, mixed.tier3_count) == (1, 1, 1, 1)
        assert mixed.jobs_created == 1 and mixed.jobs_existing == 0 and not mixed.errors
        t3_scope = next(scope for scope in mixed.scopes if scope.material_code == "T3")
        assert t3_scope.job_outcome == "CREATED" and t3_scope.priority_score is not None
        after_first = _counts(stable0["company_id"])
        assert after_first["runtime_executions"] == before["runtime_executions"]
        assert after_first["runtime_tasks"] == before["runtime_tasks"]
        assert after_first["runtime_attempts"] == before["runtime_attempts"]
        assert after_first["runtime_results"] == before["runtime_results"]
        assert after_first["artifacts"] == before["artifacts"] and after_first["leases"] == before["leases"]
        assert fits["count"] == 0

        # A material/scope failure is observable and does not suppress another
        # scope in the same bounded company scan.
        isolated_failure = RetrainingScannerService(eligibility_service_factory=_ControlledConsumptionFailure).scan(
            stable0["company_id"], "2026-W25", "2026-W32",
        )
        assert len(isolated_failure.errors) == 1
        assert isolated_failure.errors[0].demand_type == "consumption"
        assert any(scope.material_code == "T3" for scope in isolated_failure.scopes)

        # Repeated identical scan preserves tier distribution/fingerprint/job ID.
        repeat = RetrainingScannerService().scan(stable0["company_id"], "2026-W25", "2026-W32", last_seen_evaluation_ids={
            ("T0", "sales"): _watermark(stable0),
        })
        repeated_t3 = next(scope for scope in repeat.scopes if scope.material_code == "T3")
        assert repeat.jobs_existing == 1 and repeated_t3.job_id == t3_scope.job_id
        assert repeated_t3.candidate_fingerprint == t3_scope.candidate_fingerprint

        # An accepted correction reaches B1's existing correction-safe fingerprint.
        _correct(tier3, 220)
        corrected = RetrainingScannerService().scan(stable0["company_id"], "2026-W25", "2026-W32", material_codes=["T3"])
        changed = corrected.scopes[0]
        assert corrected.jobs_created == 1 and changed.job_id != t3_scope.job_id
        assert changed.candidate_fingerprint != t3_scope.candidate_fingerprint

        # Later data outside the bounded historical window does not change it.
        bounded = RetrainingScannerService().scan(stable0["company_id"], "2026-W25", "2026-W32", material_codes=["T3"])
        later = await create_tier_shape("tier3", 8, "T3", "sales", context=context, cutoff_week=40, target_start_week=41)
        bounded_again = RetrainingScannerService().scan(stable0["company_id"], "2026-W25", "2026-W32", material_codes=["T3"])
        assert (bounded.tier3_count, bounded.jobs_existing, bounded.scopes[0].job_id, bounded.scopes[0].candidate_fingerprint) == (
            bounded_again.tier3_count, bounded_again.jobs_existing, bounded_again.scopes[0].job_id,
            bounded_again.scopes[0].candidate_fingerprint,
        )

        # Separate fresh Tier-3 scope: concurrent scans must converge via B1.
        concurrent = await create_tier_shape("tier3", 8, "CONCURRENT", "sales", context=context)
        def scan_concurrent(_):
            return RetrainingScannerService().scan(stable0["company_id"], "2026-W25", "2026-W32", material_codes=["CONCURRENT"])
        with ThreadPoolExecutor(max_workers=2) as pool:
            reports = list(pool.map(scan_concurrent, range(2)))
        outcomes = [report.scopes[0].job_outcome for report in reports]
        assert sorted(outcomes) == ["ALREADY_EXISTS", "CREATED"]
        session = SessionLocal()
        try:
            assert session.query(RetrainingJob).filter_by(company_id=stable0["company_id"], material_code="CONCURRENT").count() == 1
        finally:
            session.close()

        # Company and material/demand filters never reveal the other company/scope.
        other = await create_tier_shape("tier3", 8, "OTHER", "sales"); roots.append(other)
        own = RetrainingScannerService().scan(stable0["company_id"], "2026-W25", "2026-W32", material_codes=["T2"], demand_type="sales")
        foreign = RetrainingScannerService().scan(other["company_id"], "2026-W25", "2026-W32")
        assert own.scopes_evaluated == 1 and own.scopes[0].material_code == "T2"
        assert foreign.scopes_evaluated == 1 and foreign.scopes[0].material_code == "OTHER"

        # Fresh-session reconstruction uses persisted primitive job evidence only.
        session = SessionLocal()
        try:
            persisted = session.query(RetrainingJob).filter_by(id=t3_scope.job_id, company_id=stable0["company_id"]).one()
            expected = (persisted.id, persisted.candidate_fingerprint, persisted.priority_policy_version, persisted.cooldown_policy_version)
        finally:
            session.close()
        session = SessionLocal()
        try:
            reloaded = session.query(RetrainingJob).filter_by(id=expected[0], company_id=stable0["company_id"]).one()
            assert (reloaded.id, reloaded.candidate_fingerprint, reloaded.priority_policy_version, reloaded.cooldown_policy_version) == expected
        finally:
            session.close()
        final_counts = _counts(stable0["company_id"])
        assert final_counts["leases"] == 0 and final_counts["runtime_tasks"] == before["runtime_tasks"]
        assert final_counts["artifacts"] == 0 and final_counts["decisions"] == 0
        assert final_counts["registry_entries"] == 0 and final_counts["company_learning"] == 0 and fits["count"] == 0
        print("PHASE3C4B5A PASS", {"tiers": [mixed.tier0_count, mixed.tier1_count, mixed.tier2_count, mixed.tier3_count], "jobs": [mixed.jobs_created, repeat.jobs_existing], "concurrent": outcomes, "fits": fits["count"], "leases": final_counts["leases"]})
    finally:
        xgboost.XGBRegressor.fit = original_fit
        cleaned = set()
        for root in roots:
            if root["company_id"] not in cleaned:
                cleaned.add(root["company_id"])
                _cleanup(root)
        session = SessionLocal()
        try:
            assert session.query(Company).filter(Company.id.in_(cleaned)).count() == 0
        finally:
            session.close()


if __name__ == "__main__":
    asyncio.run(main())
