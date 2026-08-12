"""PostgreSQL verification for durable, Tier-3-only retraining job acceptance."""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
print("[B1] module imports START", flush=True)

import xgboost
print("[B1] xgboost import END", flush=True)

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.forecast_evaluation_service import ForecastEvaluationService
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from scripts.support.retraining_eligibility_fixture import cleanup_fixture, create_tier_shape
print("[B1] module imports END", flush=True)


def _eligibility(fixture, watermark=None):
    session = SessionLocal()
    try:
        rows = RetrainingEligibilityService(session).evaluate(
            fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"], watermark,
        )
        return next(row for row in rows if row.material_code == fixture["material_code"])
    finally:
        session.close()


def _request(fixture, evidence):
    return RetrainingJobRequest(
        fixture["company_id"], fixture["material_code"], fixture["demand_type"], fixture["start_period"],
        fixture["end_period"], "2026-W24", evidence,
    )


def _upstream_counts(company_id):
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
            "company_learning": session.query(CompanyLearningMemory).filter_by(company_id=company_id).count(),
            "user_learning": session.query(UserLearningData).filter_by(company_id=company_id).count(),
        }
    finally:
        session.close()


def _approved_correction(fixture, quantity):
    ledger = ActualWeeklyLedgerService()
    proposed = ledger.ingest_dataset_actuals(
        fixture["company_id"], fixture["user_id"], fixture["dataset_id"], [{
            "material_code": fixture["material_code"], "period": fixture["end_period"], "quantity": quantity,
            "product_level": fixture["product_level"], "product_group": "G", "product_class": "C",
        }], fixture["demand_type"],
    )
    assert proposed["proposed"] == 1
    ledger.approve_revision(fixture["company_id"], proposed["revision_ids"][0], fixture["user_id"])
    session = SessionLocal()
    try:
        ForecastEvaluationService(session).evaluate(
            fixture["company_id"], fixture["demand_type"], fixture["start_period"], fixture["end_period"],
        )
        session.commit()
    finally:
        session.close()


def _cleanup(company_fixture):
    session = SessionLocal()
    try:
        session.query(RetrainingJob).filter_by(company_id=company_fixture["company_id"]).delete(synchronize_session=False)
        session.commit()
        cleanup_fixture(session, type("FixtureIds", (), company_fixture)())
    finally:
        session.close()


async def main():
    roots = []
    original_fit = xgboost.XGBRegressor.fit
    fit_calls = {"count": 0}
    xgboost.XGBRegressor.fit = lambda *args, **kwargs: (fit_calls.__setitem__("count", fit_calls["count"] + 1), original_fit(*args, **kwargs))[1]
    try:
        stage = time.perf_counter()
        def mark(name):
            nonlocal stage
            now = time.perf_counter()
            print(f"[B1] {name} END duration_seconds={now-stage:.2f}", flush=True)
            stage = now
            print(f"[B1] {name} NEXT", flush=True)
        print("[B1] fixture setup START", flush=True)
        tier3_x_sales = await create_tier_shape("tier3", 8, "MATERIAL_X", "sales")
        roots.append(tier3_x_sales)
        context = {name: tier3_x_sales[name] for name in ("company_id", "user_id", "dataset_id")}
        tier3_y_sales = await create_tier_shape("tier3", 8, "MATERIAL_Y", "sales", context=context)
        tier3_x_consumption = await create_tier_shape("tier3", 8, "MATERIAL_X", "consumption", context=context)
        tier3_race = await create_tier_shape("tier3", 8, "RACE", "sales", context=context)
        tier1_stable = await create_tier_shape("stable", 4, "STABLE", "sales", context=context)
        tier2 = await create_tier_shape("tier2", 8, "TIER2", "sales", context=context)
        tier3_other_company = await create_tier_shape("tier3", 8, "MATERIAL_X", "sales")
        roots.append(tier3_other_company)
        mark("fixture setup")

        service = RetrainingJobService()
        before_initial_jobs = _upstream_counts(tier3_x_sales["company_id"])
        first_evidence = _eligibility(tier3_x_sales)
        first = service.accept_candidate(_request(tier3_x_sales, first_evidence))
        repeat = service.accept_candidate(_request(tier3_x_sales, first_evidence))
        assert (first.status, repeat.status, first.job_id, repeat.job_id) == ("CREATED", "ALREADY_EXISTS", first.job_id, first.job_id)
        assert first.candidate_fingerprint == repeat.candidate_fingerprint
        mark("first and duplicate acceptance")

        t1 = _eligibility(tier1_stable)
        t0 = _eligibility(tier1_stable, t1.latest_evaluation_id)
        t2 = _eligibility(tier2)
        assert (t0.tier, t1.tier, t2.tier) == ("TIER_0_SKIP", "TIER_1_EVALUATE", "TIER_2_ANALYZE")
        assert [service.accept_candidate(_request(tier1_stable, item)).status for item in (t0, t1)] == ["NOT_ELIGIBLE", "NOT_ELIGIBLE"]
        assert service.accept_candidate(_request(tier2, t2)).status == "NOT_ELIGIBLE"
        assert before_initial_jobs == _upstream_counts(tier3_x_sales["company_id"])
        mark("tier guard assertions")

        _approved_correction(tier3_x_sales, 220)
        corrected_evidence = _eligibility(tier3_x_sales)
        before_post_correction_jobs = _upstream_counts(tier3_x_sales["company_id"])
        corrected = service.accept_candidate(_request(tier3_x_sales, corrected_evidence))
        assert corrected.status == "CREATED" and corrected.job_id != first.job_id
        assert corrected.candidate_fingerprint != first.candidate_fingerprint
        assert corrected.evaluation_evidence_fingerprint != first.evaluation_evidence_fingerprint
        mark("accepted correction fingerprint")

        different_material = service.accept_candidate(_request(tier3_y_sales, _eligibility(tier3_y_sales)))
        different_demand = service.accept_candidate(_request(tier3_x_consumption, _eligibility(tier3_x_consumption)))
        different_company = service.accept_candidate(_request(tier3_other_company, _eligibility(tier3_other_company)))
        assert [row.status for row in (different_material, different_demand, different_company)] == ["CREATED", "CREATED", "CREATED"]
        mark("scope isolation")

        barrier = threading.Barrier(2)
        race_request = _request(tier3_race, _eligibility(tier3_race))
        def contender():
            barrier.wait()
            return RetrainingJobService().accept_candidate(race_request)
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _: contender(), range(2)))
        assert sorted(row.status for row in outcomes) == ["ALREADY_EXISTS", "CREATED"]
        session = SessionLocal()
        try:
            assert session.query(RetrainingJob).filter_by(company_id=tier3_race["company_id"], candidate_fingerprint=outcomes[0].candidate_fingerprint).count() == 1
            assert session.query(RetrainingJob).filter_by(company_id=tier3_x_sales["company_id"]).count() == 5
            job = session.query(RetrainingJob).filter_by(id=corrected.job_id, company_id=tier3_x_sales["company_id"]).one()
            assert job.state == "pending" and job.runtime_execution_id is None and job.latest_evaluation_id == corrected_evidence.latest_evaluation_id
            assert RetrainingJobService().get(tier3_other_company["company_id"], corrected.job_id) is None
        finally:
            session.close()

        after = _upstream_counts(tier3_x_sales["company_id"])
        assert before_post_correction_jobs == after, {"before": before_post_correction_jobs, "after": after}
        assert fit_calls["count"] == 0
        fresh = RetrainingJobService().get(tier3_x_sales["company_id"], corrected.job_id)
        assert fresh is not None and fresh.candidate_fingerprint == corrected.candidate_fingerprint and fresh.evaluation_evidence_fingerprint == corrected.evaluation_evidence_fingerprint
        mark("concurrency and fresh session")
        print("PHASE3C4B1 PASS", {
            "created_jobs_company_a": 5, "same_evidence": repeat.status,
            "correction_fingerprint_changed": True, "concurrency": sorted(row.status for row in outcomes),
            "cross_tenant": "NOT_FOUND", "fit_calls": fit_calls["count"], "upstream_counts": after,
        })
    finally:
        cleanup_started = time.perf_counter()
        print("[B1] cleanup START", flush=True)
        xgboost.XGBRegressor.fit = original_fit
        company_ids = {root["company_id"] for root in roots}
        for root in roots:
            _cleanup(root)
        session = SessionLocal()
        try:
            assert session.query(Company).filter(Company.id.in_(company_ids)).count() == 0, "synthetic company residue remains"
        finally:
            session.close()
        print(f"[B1] cleanup END duration_seconds={time.perf_counter()-cleanup_started:.2f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
