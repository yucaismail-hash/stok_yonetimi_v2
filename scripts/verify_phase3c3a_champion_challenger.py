"""PostgreSQL proof for immutable, artifact-backed Champion--Challenger decisions."""
import asyncio
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost
from uuid_extensions import uuid7

from app.application.champion_challenger_evaluation import (
    POLICY_VERSION, THRESHOLDS, ChampionChallengerEvaluationService, ChampionEvidence,
)
from app.application.xgboost_challenger_artifacts import ArtifactIntegrityError, XGBoostChallengerArtifactService
from app.application.xgboost_challenger_training import XGBoostChallengerTrainingRequest, XGBoostChallengerTrainingService
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.company import Company, User
from app.models.model_artifact import ModelArtifact
from app.services.model_artifact_storage import LocalModelArtifactStorage
from scripts.support.champion_evidence_fixture import COMPARISON_PERIODS, cleanup, create_finished_good_sales, reconstruct


def _metrics(actuals, predictions):
    errors = [actual - prediction for actual, prediction in zip(actuals, predictions)]
    return {
        "wape": sum(abs(error) for error in errors) / sum(abs(value) for value in actuals),
        "bias": sum(errors) / len(errors),
        "mae": sum(abs(error) for error in errors) / len(errors),
        "rmse": math.sqrt(sum(error * error for error in errors) / len(errors)),
    }


def _champion(ids, evidence, label="base", sample_count=None, demand_type=None, material_code=None):
    return ChampionEvidence(
        company_id=ids.company_id,
        material_code=material_code or ids.material_code,
        demand_type=demand_type or ids.demand_type,
        model_identity=evidence.model_identity or "production_forecast",
        model_version=None,
        start_period=COMPARISON_PERIODS[0], end_period=COMPARISON_PERIODS[-1],
        sample_count=evidence.sample_count if sample_count is None else sample_count,
        metrics={"wape": float(evidence.wape), "bias": float(evidence.bias), "mae": float(evidence.mae), "rmse": float(evidence.rmse)},
        source_evidence={"fixture_evaluation_ids": [str(value) for value in evidence.evaluation_ids], "scenario": label},
    )


def main():
    storage = LocalModelArtifactStorage(Path(__file__).resolve().parents[1] / ".phase3c3a_probe_artifacts")
    ids = evidence = None
    references = []
    other_company_id = other_user_id = None
    fit_calls = {"comparison": 0}

    def train_before_forecast(company_id, user_id, dataset_id):
        session = SessionLocal()
        try:
            trainer = XGBoostChallengerTrainingService(session)
            artifacts = XGBoostChallengerArtifactService(session, storage)
            for cutoff in ("2026-W32", "2026-W31"):
                request = XGBoostChallengerTrainingRequest(
                    company_id=company_id, material_code="SKU", demand_type="sales",
                    training_cutoff_period=cutoff,
                    eligibility_evidence={"tier": "TIER_3_DEEP_LEARN_RETRAIN", "fixture": "pre_forecast"}, seed=23,
                )
                result = trainer.train(request)
                assert result.status == "TRAINED"
                persisted = artifacts.persist(request, result)
                references.append(persisted.artifact.artifact_storage_reference)
            session.commit()
            ActualWeeklyLedgerService().ingest_dataset_actuals(
                company_id, user_id, dataset_id,
                [{"material_code": "RAW", "period": f"2026-W{week:02d}", "quantity": 40 + (week % 5),
                  "product_level": "raw_material", "product_group": "RG", "product_class": "RC"}
                 for week in range(1, 33)], "consumption",
            )
            raw_request = XGBoostChallengerTrainingRequest(
                company_id=company_id, material_code="RAW", demand_type="consumption", training_cutoff_period="2026-W32",
                eligibility_evidence={"tier": "TIER_3_DEEP_LEARN_RETRAIN", "fixture": "raw_consumption"}, seed=23,
            )
            raw_result = trainer.train(raw_request); assert raw_result.status == "TRAINED"
            raw_persisted = artifacts.persist(raw_request, raw_result); references.append(raw_persisted.artifact.artifact_storage_reference)
            session.commit()
        finally:
            session.close()

    session = None
    try:
        ids, evidence, _ = asyncio.run(create_finished_good_sales(before_forecast=train_before_forecast))
        session = SessionLocal()
        artifacts = XGBoostChallengerArtifactService(session, storage)
        artifact = session.query(ModelArtifact).filter_by(
            company_id=ids.company_id, material_code="SKU", demand_type="sales", training_cutoff_period="2026-W32",
        ).one()
        corruptible = session.query(ModelArtifact).filter_by(
            company_id=ids.company_id, material_code="SKU", demand_type="sales", training_cutoff_period="2026-W31",
        ).one()
        raw_artifact = session.query(ModelArtifact).filter_by(
            company_id=ids.company_id, material_code="RAW", demand_type="consumption", training_cutoff_period="2026-W32",
        ).one()
        # Trusted load is mandatory and comparison itself may never fit XGBoost.
        original_fit = xgboost.XGBRegressor.fit
        def counted_fit(*args, **kwargs):
            fit_calls["comparison"] += 1
            return original_fit(*args, **kwargs)
        xgboost.XGBRegressor.fit = counted_fit
        try:
            model = artifacts.load(ids.company_id, artifact.id)
            # The loaded model generates same-window predictions.  Policy test
            # cases below supply deterministic same-window metric evidence to
            # the decision boundary, whose explicit contract accepts metrics.
            values = [100 + (week % 7) for week in range(1, 33)]
            predictions = []
            for week in range(33, 38):
                history = values[-8:]
                x = [history[-1], history[-2], history[-3], history[-4], sum(history[-4:]) / 4,
                     math.sqrt(sum((value - sum(history[-4:]) / 4) ** 2 for value in history[-4:]) / 4),
                     sum(history) / 8, math.sqrt(sum((value - sum(history) / 8) ** 2 for value in history) / 8),
                     float(week), math.sin(2 * math.pi * week / 53), math.cos(2 * math.pi * week / 53), float(len(values)), 0.0, 0.0]
                value = float(model.predict([x])[0]); values.append(value); predictions.append(value)
            actuals = [134.0, 135.0, 136.0, 137.0]
            same_window_metrics = _metrics(actuals, predictions[1:])
            assert len(predictions) == 5 and all(math.isfinite(value) for value in predictions)

            service = ChampionChallengerEvaluationService(session, artifacts)
            champion = _champion(ids, evidence, "promote")
            promote_metrics = {"wape": float(evidence.wape) * .50, "bias": float(evidence.bias), "mae": float(evidence.mae) * .50, "rmse": float(evidence.rmse) * .50}
            promote = service.compare(champion, artifact.id, promote_metrics)
            assert promote.decision == "PROMOTE_CHALLENGER"
            session.commit()
            same = service.compare(champion, artifact.id, promote_metrics)
            assert same.id == promote.id and session.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).count() == 1

            keep = service.compare(_champion(ids, evidence, "keep"), artifact.id, {"wape": float(evidence.wape) * 1.1, "bias": float(evidence.bias), "mae": float(evidence.mae), "rmse": float(evidence.rmse)})
            bias = service.compare(_champion(ids, evidence, "bias"), artifact.id, {"wape": float(evidence.wape) * .50, "bias": abs(float(evidence.bias)) + THRESHOLDS["max_bias_regression"] + .01, "mae": float(evidence.mae) * .50, "rmse": float(evidence.rmse) * .50})
            insufficient = service.compare(_champion(ids, evidence, "insufficient", sample_count=3), artifact.id, promote_metrics)
            assert keep.decision == "KEEP_CHAMPION" and "INSUFFICIENT_WAPE_IMPROVEMENT" in keep.reason_codes
            assert bias.decision == "KEEP_CHAMPION" and "BIAS_GUARDRAIL" in bias.reason_codes
            assert insufficient.decision == "INSUFFICIENT_EVIDENCE" and "INSUFFICIENT_SAMPLE" in insufficient.reason_codes
            raw_champion = ChampionEvidence(
                ids.company_id, "RAW", "consumption", "production_forecast", None,
                COMPARISON_PERIODS[0], COMPARISON_PERIODS[-1], 4,
                {"wape": .10, "bias": .01, "mae": 4.0, "rmse": 5.0},
                {"scenario": "raw_consumption", "product_level": "raw_material"},
            )
            raw_decision = service.compare(raw_champion, raw_artifact.id, {"wape": .04, "bias": .01, "mae": 2.0, "rmse": 2.5})
            assert raw_decision.decision == "PROMOTE_CHALLENGER"
            try:
                service.compare(ChampionEvidence(ids.company_id, "SKU", "consumption", "x", None, COMPARISON_PERIODS[0], COMPARISON_PERIODS[-1], 4, champion.metrics, {"scenario": "cross_demand"}), artifact.id, promote_metrics)
                raise AssertionError("cross-demand comparison was allowed")
            except ValueError as exc:
                assert str(exc) == "CHALLENGER_SCOPE_MISMATCH"
            session.commit()
            first_snapshot = (promote.decision, promote.challenger_metrics, promote.reason_codes)
            try:
                promote.decision = "KEEP_CHAMPION"; session.flush(); raise AssertionError("decision update was allowed")
            except ValueError as exc:
                assert str(exc) == "ChampionChallengerDecision is immutable"; session.rollback()
            session.refresh(promote); assert first_snapshot == (promote.decision, promote.challenger_metrics, promote.reason_codes)

            # Probe-only controlled corruption fails before a decision is written.
            before_corrupt = session.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).count()
            (storage.base_directory / corruptible.artifact_storage_reference).write_bytes(b"corrupt")
            try:
                service.compare(_champion(ids, evidence, "corrupt"), corruptible.id, promote_metrics)
                raise AssertionError("corrupt artifact reached decision creation")
            except ArtifactIntegrityError as exc:
                assert str(exc) == "ARTIFACT_INTEGRITY_ERROR"
            assert session.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).count() == before_corrupt

            # A second tenant cannot obtain A's artifact or create a decision from it.
            other = Company(id=uuid7(), name="phase3c3a_other_" + str(uuid7()), tax_id="phase3c3a_other_" + str(uuid7()))
            other_user = User(id=uuid7(), company_id=other.id, email=str(other.id) + "@x.invalid", hashed_password="x")
            session.add_all((other, other_user)); session.commit(); other_company_id, other_user_id = other.id, other_user.id
            foreign = ChampionEvidence(other.id, "SKU", "sales", "x", None, COMPARISON_PERIODS[0], COMPARISON_PERIODS[-1], 4, champion.metrics, {"scenario": "tenant"})
            try:
                service.compare(foreign, artifact.id, promote_metrics); raise AssertionError("cross-tenant comparison was allowed")
            except LookupError as exc:
                assert str(exc) == "MODEL_ARTIFACT_NOT_FOUND"
            assert session.query(ChampionChallengerDecision).filter_by(company_id=other_company_id).count() == 0
        finally:
            xgboost.XGBRegressor.fit = original_fit

        session.close(); session = SessionLocal()
        loaded_decisions = session.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).order_by(ChampionChallengerDecision.created_at).all()
        assert len(loaded_decisions) == 5 and reconstruct(session, ids).target_periods == evidence.target_periods
        assert fit_calls["comparison"] == 0
        assert all(row.policy_version == POLICY_VERSION and row.thresholds == THRESHOLDS for row in loaded_decisions)
        print("PHASE3C3A PASS", {"decisions": len(loaded_decisions), "same_window_wape": round(same_window_metrics["wape"], 6), "comparison_fit_calls": 0, "xgboost": xgboost.__version__})
    finally:
        if session is not None:
            if ids is not None:
                session.query(ChampionChallengerDecision).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
                for reference in references: storage.delete_for_controlled_cleanup(reference)
                session.query(ModelArtifact).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
                if other_user_id is not None:
                    session.query(User).filter_by(id=other_user_id).delete(synchronize_session=False)
                    session.query(Company).filter_by(id=other_company_id).delete(synchronize_session=False)
                session.commit()
                cleanup(session, ids)
            else: session.close()


if __name__ == "__main__": main()
