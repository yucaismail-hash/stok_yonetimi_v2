"""Focused PostgreSQL proof for cutoff-safe recursive Champion inference."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost
from uuid_extensions import uuid7

from app.analysis.forecast import DemandForecaster
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.champion_promotion import ChampionPromotionService
from app.application.champion_registry import ChampionRegistryService
from app.application.champion_resolver import ChampionResolver
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.application.xgboost_champion_inference import XGBoostChampionInferenceService
from app.application.xgboost_weekly_features import FEATURE_SCHEMA_VERSION
from app.database import SessionLocal
from app.engine.adapters.forecast_adapter import forecast_adapter
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_registry import Capability
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.learning import CompanyLearningMemory, UserLearningData
from app.models.model_artifact import ModelArtifact
from app.models.runtime import RuntimeResultReference, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.model_artifact_storage import LocalModelArtifactStorage
from app.services.security import EncryptionService


def _counts(session, company_id):
    return {
        "actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
        "revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
        "vintages": session.query(ForecastVintage).filter_by(company_id=company_id).count(),
        "evaluations": session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
        "result_references": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
        "task_attempts": session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
        "registry_entries": session.query(ChampionRegistryEntry).filter_by(company_id=company_id).count(),
        "registry_transitions": session.query(ChampionRegistryTransition).filter_by(company_id=company_id).count(),
        "registry_current": session.query(ChampionRegistryCurrent).filter_by(company_id=company_id).count(),
        "artifacts": session.query(ModelArtifact).filter_by(company_id=company_id).count(),
        "decisions": session.query(ChampionChallengerDecision).filter_by(company_id=company_id).count(),
        "company_learning": session.query(CompanyLearningMemory).filter_by(company_id=company_id).count(),
        "user_learning": session.query(UserLearningData).filter_by(company_id=company_id).count(),
    }


def _persist_artifact(session, storage, company_id, material_code, cutoff):
    # Native UBJ has the deployed 14-column contract and a deterministic base
    # prediction, without fitting any model during this inference-only proof.
    model = xgboost.Booster(); model.set_param({"num_feature": 14, "objective": "reg:squarederror"})
    artifact_id = uuid7(); payload = bytes(model.save_raw(raw_format="ubj"))
    reference = storage.write(company_id, artifact_id, payload)
    artifact = ModelArtifact(
        id=artifact_id, company_id=company_id, material_code=material_code, demand_type="sales",
        model_role="challenger", model_family="xgboost", model_version="fixture-v1",
        artifact_contract_version="1", xgboost_version=xgboost.__version__,
        feature_schema_version=FEATURE_SCHEMA_VERSION, encoding_contract_version="explicit_category_codes_v1",
        split_policy_version="time_ordered_holdout_v1", training_cutoff_period=cutoff,
        training_period_start="2026-W09", training_period_end="2026-W28",
        validation_period_start="2026-W29", validation_period_end=cutoff,
        training_sample_count=20, validation_sample_count=4, seed=7, model_parameters={},
        artifact_storage_reference=reference, artifact_checksum=hashlib.sha256(payload).hexdigest(),
        artifact_size_bytes=len(payload), source_actual_observation_ids=[],
        source_evidence_signature="x" * 64, artifact_fingerprint=str(uuid7()).replace("-", ""),
    )
    session.add(artifact); session.flush()
    return artifact, reference


def _promote(session, storage, company_id, material_code, product_level, artifact):
    decision = ChampionChallengerDecision(
        company_id=company_id, material_code=material_code, demand_type="sales",
        challenger_model_artifact_id=artifact.id,
        champion_evidence={"product_metadata": {"product_level": product_level}},
        comparison_start_period="2026-W33", comparison_end_period="2026-W37", sample_count=4,
        champion_metrics={}, challenger_metrics={}, policy_version="champion_challenger_policy_v1",
        thresholds={}, decision="PROMOTE_CHALLENGER", reason_codes=[],
        comparison_fingerprint=str(uuid7()).replace("-", ""),
    )
    session.add(decision); session.commit()
    current = ChampionRegistryService().bootstrap(company_id, material_code, "sales", product_level)
    outcome = ChampionPromotionService(
        artifact_service_factory=lambda db: XGBoostChallengerArtifactService(db, storage)
    ).promote(company_id, decision.id, current.active_entry_id, current.row_version)
    assert outcome.status == "PROMOTED"
    return decision, outcome.active_entry_id


def _cleanup(session, storage, company_id, user_id, references):
    session.rollback()
    for reference in references:
        storage.delete_for_controlled_cleanup(reference)
    session.query(ChampionRegistryCurrent).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(ChampionRegistryTransition).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(ChampionRegistryEntry).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(ChampionChallengerDecision).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(ModelArtifact).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(Dataset).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(CompanyEncryptionKey).filter_by(user_id=user_id).delete(synchronize_session=False)
    session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
    session.query(Company).filter_by(id=company_id).delete(synchronize_session=False)
    session.commit()
    assert session.query(Company).filter_by(id=company_id).count() == 0
    assert session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count() == 0
    assert session.query(ModelArtifact).filter_by(company_id=company_id).count() == 0


def main():
    session = SessionLocal(); company_id = user_id = None; references = []
    storage = LocalModelArtifactStorage(Path(__file__).resolve().parents[1] / ".phase3c3b3a_inference_artifacts")
    calls = {"fit": 0, "predict": 0, "resolver": 0}; prediction_rows = []
    try:
        tag = "phase3c3b3ai1_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.flush(); company_id, user_id = company.id, user.id
        dataset = Dataset(id=uuid7(), company_id=company_id, user_id=user_id, uploaded_by=user_id,
                          dataset_hash=hashlib.sha256(tag.encode()).hexdigest(), source_type=tag,
                          encrypted_data=EncryptionService(session).encrypt_dataset(user_id, {"items": []}), is_active=True)
        session.add(dataset); session.commit()
        ledger = ActualWeeklyLedgerService()
        ledger.ingest_dataset_actuals(company_id, user_id, dataset.id, [
            {"material_code": "SKU", "period": f"2026-W{week:02d}", "quantity": 100 + week,
             "product_level": "finished_good"} for week in range(1, 38)
        ], "sales")
        artifact, reference = _persist_artifact(session, storage, company_id, "SKU", "2026-W32"); references.append(reference)
        decision, entry_id = _promote(session, storage, company_id, "SKU", "finished_good", artifact)
        baseline_counts = _counts(session, company_id)

        original_fit, original_predict = xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict
        def counted_fit(*args, **kwargs): calls["fit"] += 1; return original_fit(*args, **kwargs)
        def counted_predict(*args, **kwargs):
            calls["predict"] += 1; prediction_rows.append(tuple(float(value) for value in args[1][0]))
            return original_predict(*args, **kwargs)
        xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict = counted_fit, counted_predict
        try:
            resolver = ChampionResolver(
                artifact_service_factory=lambda db: XGBoostChallengerArtifactService(db, storage)
            )
            inference = XGBoostChampionInferenceService(
                resolver=resolver,
                artifact_service_factory=lambda db: XGBoostChallengerArtifactService(db, storage)
            )
            first = inference.predict(company_id, "SKU", "sales", "2026-W32", 5)
            repeat = inference.predict(company_id, "SKU", "sales", "2026-W32", 5)
        finally:
            xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict = original_fit, original_predict
        assert first.target_periods == ("2026-W33", "2026-W34", "2026-W35", "2026-W36", "2026-W37")
        assert first.forecast_values == repeat.forecast_values and first.recursive_input_counts == (32, 33, 34, 35, 36)
        assert first.champion_registry_entry_id == entry_id and first.model_artifact_id == artifact.id
        assert first.artifact_checksum == artifact.artifact_checksum and first.training_cutoff_period == "2026-W32"
        assert first.feature_schema_version == FEATURE_SCHEMA_VERSION and first.inference_strategy_version == "recursive_weekly_v1"
        assert calls == {"fit": 0, "predict": 10, "resolver": 0}
        assert prediction_rows[1][0] == first.forecast_values[0]
        assert prediction_rows[2][0:2] == (first.forecast_values[1], first.forecast_values[0])
        assert _counts(session, company_id) == baseline_counts

        changes = ledger.ingest_dataset_actuals(company_id, user_id, dataset.id, [
            {"material_code": "SKU", "period": f"2026-W{week:02d}", "quantity": 9000 + week,
             "product_level": "finished_good"} for week in range(33, 38)
        ], "sales")
        for revision_id in changes["revision_ids"]:
            ledger.approve_revision(company_id, revision_id, user_id)
        after_future = inference.predict(company_id, "SKU", "sales", "2026-W32", 5)
        assert after_future == first

        # The public probe evidence counts the evolving recursive history: W34
        # starts with predicted W33, and all later rows include prior predictions.
        assert first.recursive_input_counts[1:] == (33, 34, 35, 36)

        ledger.ingest_dataset_actuals(company_id, user_id, dataset.id, [
            {"material_code": "SHORT", "period": f"2026-W{week:02d}", "quantity": week,
             "product_level": "finished_good"} for week in range(1, 8)
        ], "sales")
        short_artifact, short_reference = _persist_artifact(session, storage, company_id, "SHORT", "2026-W07"); references.append(short_reference)
        _promote(session, storage, company_id, "SHORT", "finished_good", short_artifact)
        try:
            inference.predict(company_id, "SHORT", "sales", "2026-W07", 1)
            raise AssertionError("short history unexpectedly predicted")
        except ValueError as exc:
            assert str(exc) == "NOT_PREDICTABLE"

        # A valid ISO W53 rollover is generated by the same canonical target utility used in inference.
        ledger.ingest_dataset_actuals(company_id, user_id, dataset.id, [
            {"material_code": "W53", "period": period, "quantity": index + 1,
             "product_level": "finished_good"}
            for index, period in enumerate(("2020-W46", "2020-W47", "2020-W48", "2020-W49", "2020-W50", "2020-W51", "2020-W52", "2020-W53"))
        ], "sales")
        w53_artifact, w53_reference = _persist_artifact(session, storage, company_id, "W53", "2020-W53"); references.append(w53_reference)
        _promote(session, storage, company_id, "W53", "finished_good", w53_artifact)
        rollover = inference.predict(company_id, "W53", "sales", "2020-W53", 2)
        assert rollover.target_periods == ("2021-W01", "2021-W02") and rollover.recursive_input_counts == (8, 9)

        original_resolve = ChampionResolver.resolve
        def counted_resolve(*args, **kwargs): calls["resolver"] += 1; return original_resolve(*args, **kwargs)
        ChampionResolver.resolve = counted_resolve
        original_fit, original_predict = xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict
        xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict = counted_fit, counted_predict
        try:
            request = CapabilityExecutionRequest(uuid7(), "i1-non-impact", "forecast", Capability.DEMAND_FORECAST,
                                                 company_id, user_id, dataset.id, 30, params={"horizon": 2})
            normal = forecast_adapter(DemandForecaster, {"items": [{"material_code": "SKU", "demand_history": list(range(10, 30))}]}, request)
            assert normal["items"][0]["model_used"] in {"holt_winters", "arima", "simple"}
        finally:
            ChampionResolver.resolve = original_resolve
            xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict = original_fit, original_predict
        assert calls["resolver"] == 0 and calls["fit"] == 0 and calls["predict"] == 10
        print("PHASE 3C3B3A-I1 PASS", {"targets": first.target_periods, "artifact": str(artifact.id), "entry": str(entry_id), "xgboost": xgboost.__version__, "recursive_history": first.recursive_input_counts})
    finally:
        if company_id:
            _cleanup(session, storage, company_id, user_id, references)
        session.close()


if __name__ == "__main__":
    main()
