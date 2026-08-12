"""PostgreSQL closeout for the read-only PHASE 3C1 eligibility contract."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.forecast_evaluation_service import ForecastEvaluationService
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape


def _read(fixture, watermark=None):
    session = SessionLocal()
    try:
        result = RetrainingEligibilityService(session).evaluate(
            fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"], watermark,
        )
        scoped = [item for item in result if item.material_code == fixture["material_code"]]
        assert len(scoped) == 1, f"missing or duplicated scoped material result: {fixture['material_code']!r} in {result!r}"
        return scoped[0]
    finally:
        session.close()


def _counts(company_id):
    session = SessionLocal()
    try:
        return {
            "actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
            "actual_revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
            "forecast_vintages": session.query(ForecastVintage).filter_by(company_id=company_id).count(),
            "forecast_evaluations": session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
            "runtime_executions": session.query(RuntimeExecution).filter_by(company_id=company_id).count(),
            "runtime_tasks": session.query(RuntimeTask).filter_by(company_id=company_id).count(),
            "runtime_task_attempts": session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
            "runtime_result_references": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
            "model_artifacts": session.query(ModelArtifact).filter_by(company_id=company_id).count(),
            "registry_entries": session.query(ChampionRegistryEntry).filter_by(company_id=company_id).count(),
            "registry_current": session.query(ChampionRegistryCurrent).filter_by(company_id=company_id).count(),
            "registry_transitions": session.query(ChampionRegistryTransition).filter_by(company_id=company_id).count(),
            "company_learning": session.query(CompanyLearningMemory).filter_by(company_id=company_id).count(),
            "user_learning": session.query(UserLearningData).filter_by(company_id=company_id).count(),
        }
    finally:
        session.close()


def _refresh(fixture):
    session = SessionLocal()
    try:
        resolution = ForecastEvaluationService(session).evaluate(
            fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"],
        )
        session.commit()
        assert resolution.evaluation.id == fixture["evaluation_id"]
    finally:
        session.close()


def _correct(fixture, period, quantity, approve):
    row = {
        "material_code": fixture["material_code"], "period": period, "quantity": quantity,
        "product_level": fixture["product_level"], "product_group": "G", "product_class": "C",
    }
    ledger = ActualWeeklyLedgerService()
    proposed = ledger.ingest_dataset_actuals(
        fixture["company_id"], fixture["user_id"], fixture["dataset_id"], [row], fixture["demand_type"],
    )
    assert proposed["proposed"] == 1 and len(proposed["revision_ids"]) == 1
    decision = (ledger.approve_revision if approve else ledger.reject_revision)(
        fixture["company_id"], proposed["revision_ids"][0], fixture["user_id"],
    )
    assert decision == proposed["revision_ids"][0]


async def main():
    cleanup_companies = []
    original_fit = xgboost.XGBRegressor.fit
    fit_calls = {"count": 0}
    xgboost.XGBRegressor.fit = lambda *args, **kwargs: (fit_calls.__setitem__("count", fit_calls["count"] + 1), original_fit(*args, **kwargs))[1]
    try:
        # Company A contains the three distinct registry-independent eligibility scopes.
        a_x_sales = await create_tier_shape("stable", 4, "MATERIAL_X", "sales")
        cleanup_companies.append(a_x_sales)
        a_context = {key: a_x_sales[key] for key in ("company_id", "user_id", "dataset_id")}
        a_x_consumption = await create_tier_shape("stable", 4, "MATERIAL_X", "consumption", context=a_context)
        a_y_sales = await create_tier_shape("tier2", 8, "MATERIAL_Y", "sales", context=a_context, cutoff_week=32, target_start_week=33)
        b_x_sales = await create_tier_shape("stable", 4, "MATERIAL_X", "sales")
        cleanup_companies.append(b_x_sales)
        tier3 = await create_tier_shape("tier3", 8, "TIER3", "sales", "finished_good")
        cleanup_companies.append(tier3)
        raw = await create_tier_shape("tier3", 8, "RAW", "consumption", "raw_material")
        cleanup_companies.append(raw)

        # Independent scope/watermark contract.
        first = [_read(fixture) for fixture in (a_x_sales, a_x_consumption, a_y_sales, b_x_sales)]
        assert [item.tier for item in first] == ["TIER_1_EVALUATE", "TIER_1_EVALUATE", "TIER_2_ANALYZE", "TIER_1_EVALUATE"]
        assert all(item.new_evidence_detected for item in first)
        assert len({item.latest_evaluation_id for item in first}) == 4
        repeated = [_read(fixture, item.latest_evaluation_id) for fixture, item in zip((a_x_sales, a_x_consumption, a_y_sales, b_x_sales), first)]
        assert [item.tier for item in repeated] == ["TIER_0_SKIP", "TIER_0_SKIP", "TIER_2_ANALYZE", "TIER_0_SKIP"]
        assert [item.new_evidence_detected for item in repeated] == [False, False, False, False]

        # Product level is preserved metadata rather than a material grouping key.
        raw_result = _read(raw)
        tier3_before = _read(tier3)
        assert (raw_result.product_level, raw_result.demand_type, raw_result.tier) == ("raw_material", "consumption", "TIER_3_DEEP_LEARN_RETRAIN")
        assert (tier3_before.product_level, tier3_before.demand_type, tier3_before.tier) == ("finished_good", "sales", "TIER_3_DEEP_LEARN_RETRAIN")
        assert ActualWeeklyLedgerService._row({"material_code": "SEMIFINISHED", "period": "2026-W01", "quantity": 1, "product_level": "semi_finished_good"}, "sales")["product_level"] == "semi_finished_good"

        # Later persisted evaluation evidence cannot affect a bounded historical read.
        bounded = _read(a_x_sales, first[0].latest_evaluation_id)
        later = await create_tier_shape("stable", 4, "MATERIAL_X", "sales", context=a_context, cutoff_week=32, target_start_week=33)
        assert later["evaluation_id"] != a_x_sales["evaluation_id"]
        assert _read(a_x_sales, first[0].latest_evaluation_id) == bounded

        # Canonical accepted correction updates the evidence point; rejected correction does not.
        _correct(tier3, tier3["end_period"], 220, approve=True)
        _refresh(tier3)
        accepted = _read(tier3)
        assert accepted != tier3_before and accepted.tier == "TIER_3_DEEP_LEARN_RETRAIN"
        session = SessionLocal()
        try:
            point = session.query(ActualWeeklyObservation).filter_by(company_id=tier3["company_id"], material_code=tier3["material_code"], demand_type="sales", period=tier3["end_period"]).one()
            assert point.quantity == 220
        finally:
            session.close()
        _correct(tier3, tier3["end_period"], 280, approve=False)
        _refresh(tier3)
        rejected = _read(tier3)
        assert rejected == accepted

        # Eligibility is deterministic and entirely read-only, including at Tier 3.
        before_counts = _counts(tier3["company_id"])
        first_tier3 = _read(tier3, accepted.latest_evaluation_id)
        second_tier3 = _read(tier3, accepted.latest_evaluation_id)
        after_counts = _counts(tier3["company_id"])
        assert first_tier3 == second_tier3
        assert before_counts == after_counts, {"before": before_counts, "after": after_counts}
        assert fit_calls["count"] == 0

        # Genuine fresh session/service reconstruction uses only persisted primitive fixture ids.
        expected = first_tier3
        fresh_session = SessionLocal()
        try:
            fresh = RetrainingEligibilityService(fresh_session).evaluate(
                tier3["company_id"], tier3["demand_type"], tier3["start_period"], tier3["end_period"], accepted.latest_evaluation_id,
            )[0]
        finally:
            fresh_session.close()
        assert fresh == expected

        print("PHASE3C1 MATRIX CLOSEOUT PASS", {
            "isolation": [(item.company_id, item.material_code, item.demand_type, item.tier) for item in first],
            "bounded_window": bounded.latest_evaluation_id,
            "accepted_correction_wape": str(accepted.current_wape),
            "tier3_fresh": fresh.tier,
            "read_only_counts": before_counts,
            "xgboost_fit_calls": fit_calls["count"],
        })
    finally:
        xgboost.XGBRegressor.fit = original_fit
        cleaned = set()
        for fixture in cleanup_companies:
            if fixture["company_id"] in cleaned:
                continue
            cleaned.add(fixture["company_id"])
            session = SessionLocal()
            try:
                cleanup_fixture(session, type("FixtureIds", (), fixture)())
            finally:
                session.close()
        session = SessionLocal()
        try:
            assert session.query(Company).filter(Company.id.in_(cleaned)).count() == 0, "synthetic company residue remains"
        finally:
            session.close()


if __name__ == "__main__":
    asyncio.run(main())
