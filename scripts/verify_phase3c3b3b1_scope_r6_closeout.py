"""PostgreSQL closeout proof for production Champion Forecast scope."""
import asyncio
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost
from uuid_extensions import uuid7

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.business_workflow_acceptance import BusinessWorkflowAcceptanceService
from app.application.champion_promotion import ChampionPromotionService
from app.application.champion_registry import ChampionRegistryService
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.application.xgboost_champion_inference import XGBoostChampionInferenceService
from app.application.xgboost_weekly_features import FEATURE_SCHEMA_VERSION
from app.database import SessionLocal
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.engine.local_forecast_runner import LocalForecastRunner
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.model_artifact import ModelArtifact
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.model_artifact_storage import LocalModelArtifactStorage
from app.services.security import EncryptionService


def _artifact(session, company_id, material_code, demand_type, level, storage_refs):
    artifact_id = uuid7()
    booster = xgboost.Booster()
    booster.set_param({"num_feature": 14, "objective": "reg:squarederror"})
    binary = bytes(booster.save_raw(raw_format="ubj"))
    ref = LocalModelArtifactStorage().write(company_id, artifact_id, binary)
    storage_refs.append(ref)
    artifact = ModelArtifact(
        id=artifact_id, company_id=company_id, material_code=material_code, demand_type=demand_type,
        model_role="challenger", model_family="xgboost", model_version="r6-fixture-v1",
        artifact_contract_version="1", xgboost_version=xgboost.__version__,
        feature_schema_version=FEATURE_SCHEMA_VERSION, encoding_contract_version="explicit_category_codes_v1",
        split_policy_version="time_ordered_holdout_v1", training_cutoff_period="2026-W32",
        training_period_start="2026-W09", training_period_end="2026-W28",
        validation_period_start="2026-W29", validation_period_end="2026-W32",
        training_sample_count=20, validation_sample_count=4, seed=1, model_parameters={},
        artifact_storage_reference=ref, artifact_checksum=hashlib.sha256(binary).hexdigest(),
        artifact_size_bytes=len(binary), source_actual_observation_ids=[], source_evidence_signature="a" * 64,
        artifact_fingerprint=hashlib.sha256((material_code + demand_type + str(artifact_id)).encode()).hexdigest(),
    )
    session.add(artifact)
    session.flush()
    current = ChampionRegistryService().bootstrap(company_id, material_code, demand_type, level)
    decision = ChampionChallengerDecision(
        company_id=company_id, material_code=material_code, demand_type=demand_type,
        challenger_model_artifact_id=artifact_id, champion_evidence={"product_metadata": {"product_level": level}},
        comparison_start_period="2026-W33", comparison_end_period="2026-W34", sample_count=4,
        champion_metrics={}, challenger_metrics={}, policy_version="champion_challenger_policy_v1", thresholds={},
        decision="PROMOTE_CHALLENGER", reason_codes=[], comparison_fingerprint=hashlib.sha256(("decision" + material_code + demand_type + str(artifact_id)).encode()).hexdigest(),
    )
    session.add(decision)
    session.commit()
    promoted = ChampionPromotionService().promote(company_id, decision.id, current.active_entry_id, current.row_version)
    assert promoted.status == "PROMOTED"
    return artifact_id


async def _complete_business(execution_id, company_id):
    completed = []
    while True:
        session = SessionLocal()
        try:
            ready = [row for row in BusinessWorkflowScheduler(session).readiness(execution_id, company_id) if row["ready"]]
        finally:
            session.close()
        if not ready:
            return completed
        completed.append(ready[0]["task_id"])
        reference = await LocalForecastRunner().run_business_task(execution_id, company_id, ready[0]["task_id"])
        assert reference is not None


def _scoped_forecast(company_id, user_id, dataset_id, material_code, demand_type, level):
    params = {"horizon": 2, "forecast_vintage": {"demand_type": demand_type, "product_metadata": {material_code: {"product_level": level}}}}
    dispatched = asyncio.run(WorkflowDispatcher().dispatch_single_analysis(company_id, user_id, dataset_id, "forecast", [material_code], params))
    reference = asyncio.run(LocalForecastRunner().run(dispatched["execution_id"]))
    return dispatched["execution_id"], reference


def main():
    session = SessionLocal()
    cid = uid = None
    storage_refs = []
    try:
        tag = "phase3c3b3b1_r6_" + str(uuid7())
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user)); session.flush(); cid, uid = company.id, user.id
        specs = (("FG", "sales", "finished_good"), ("RM", "consumption", "raw_material"), ("SFG", "sales", "semi_finished_good"))
        datasets = {}
        for code, demand, level in specs:
            payload = {"items": [{"sku_code": code, "demand_history": [100 + week for week in range(32)], "lead_time_days": 7, "initial_stock": 500, "eoq": 100}]}
            dataset = Dataset(id=uuid7(), company_id=cid, user_id=uid, uploaded_by=uid, dataset_hash=hashlib.sha256((tag + code).encode()).hexdigest(), source_type=tag, encrypted_data=EncryptionService(session).encrypt_dataset(uid, payload), is_active=True)
            session.add(dataset); datasets[code] = dataset.id
        session.commit()
        ledger = ActualWeeklyLedgerService()
        for code, demand, level in specs:
            ledger.ingest_dataset_actuals(cid, uid, datasets[code], [{"material_code": code, "period": f"2026-W{week:02d}", "quantity": 100 + week, "product_level": level} for week in range(1, 33)], demand)
        session.close(); session = SessionLocal()
        artifacts = {(code, demand): _artifact(session, cid, code, demand, level, storage_refs) for code, demand, level in specs}

        counters = {"fit": 0, "champion_predict": 0}
        original_fit, original_predict = xgboost.XGBRegressor.fit, XGBoostChampionInferenceService.predict
        xgboost.XGBRegressor.fit = lambda *args, **kwargs: (counters.__setitem__("fit", counters["fit"] + 1), original_fit(*args, **kwargs))[1]
        XGBoostChampionInferenceService.predict = lambda self, *args, **kwargs: (counters.__setitem__("champion_predict", counters["champion_predict"] + 1), original_predict(self, *args, **kwargs))[1]
        try:
            business = BusinessWorkflowAcceptanceService().accept_or_resolve(cid, uid, datasets["FG"], request_metadata={"params": {"horizon": 2, "forecast_vintage": {"demand_type": "sales", "product_metadata": {"FG": {"product_level": "finished_good"}}}}})
            assert business.status == "CREATED"
            tasks = asyncio.run(_complete_business(business.execution_id, cid))
            assert tasks == ["forecast", "safety_stock", "simulation", "backtest"]
            business_predicts = counters["champion_predict"]
            assert business_predicts == 1
            matrix = {}
            for code, demand, level in specs:
                execution_id, reference = _scoped_forecast(cid, uid, datasets[code], code, demand, level)
                matrix[code] = (execution_id, reference.id)
        finally:
            xgboost.XGBRegressor.fit = original_fit
            XGBoostChampionInferenceService.predict = original_predict
        assert counters["fit"] == 0 and counters["champion_predict"] == 4

        session.close(); session = SessionLocal()
        execution = session.query(RuntimeExecution).filter_by(execution_id=business.execution_id, company_id=cid).one()
        business_params = execution.metadata_["request_metadata"]["params"]
        assert execution.state == "completed" and float(execution.progress) == 100.0
        refs = {ref.result_type: ref for ref in session.query(RuntimeResultReference).filter_by(execution_id=business.execution_id, company_id=cid).all()}
        assert set(refs) == {"forecast", "safety_stock", "simulation", "backtest"}
        forecast = refs["forecast"].inline_result["items"][0]
        info = forecast["selection_info"]
        vintage = session.query(ForecastVintage).filter_by(runtime_result_reference_id=refs["forecast"].id).one()
        points = session.query(ForecastVintagePoint).filter_by(forecast_vintage_id=vintage.id).order_by(ForecastVintagePoint.horizon_index).all()
        fg_artifact_id = artifacts[("FG", "sales")]
        assert forecast["model_used"] == "xgboost_champion" and info["champion_resolution"] == "xgboost_artifact"
        assert info["model_artifact_id"] == str(fg_artifact_id) and info["demand_type"] == business_params["demand_type"] == vintage.demand_type == "sales"
        assert info["forecast_cutoff_period"] == business_params["forecast_cutoff_period"] == vintage.input_cutoff_period == "2026-W32" and len(points) == 2
        for code, demand, level in specs:
            execution_id, reference_id = matrix[code]
            scoped_execution = session.query(RuntimeExecution).filter_by(execution_id=execution_id, company_id=cid).one()
            scoped_params = scoped_execution.metadata_["params"]
            item = session.query(RuntimeResultReference).filter_by(id=reference_id).one().inline_result["items"][0]
            scoped_vintage = session.query(ForecastVintage).filter_by(runtime_result_reference_id=reference_id).one()
            assert item["model_used"] == "xgboost_champion" and item["selection_info"]["demand_type"] == scoped_params["demand_type"] == scoped_vintage.demand_type == demand
            assert item["selection_info"]["forecast_cutoff_period"] == scoped_params["forecast_cutoff_period"] == scoped_vintage.input_cutoff_period == "2026-W32"
            assert item["selection_info"]["model_artifact_id"] == str(artifacts[(code, demand)])
        business_id, forecast_ref_id, vintage_id = business.execution_id, refs["forecast"].id, vintage.id
        session.close(); session = SessionLocal()
        fresh_execution = session.query(RuntimeExecution).filter_by(execution_id=business_id, company_id=cid).one()
        fresh_refs = session.query(RuntimeResultReference).filter_by(execution_id=business_id, company_id=cid).all()
        fresh_forecast = session.query(RuntimeResultReference).filter_by(id=forecast_ref_id).one()
        fresh_vintage = session.query(ForecastVintage).filter_by(id=vintage_id).one()
        assert fresh_execution.state == "completed" and float(fresh_execution.progress) == 100.0 and len(fresh_refs) == 4
        assert fresh_forecast.inline_result["items"][0]["selection_info"]["model_artifact_id"] == str(fg_artifact_id)
        assert fresh_vintage.runtime_result_reference_id == forecast_ref_id and len(session.query(ForecastVintagePoint).filter_by(forecast_vintage_id=vintage_id).all()) == 2
        print("PHASE 3C3B3B1 R6 PASS", {"business_execution_id": str(business_id), "tasks": tasks, "matrix": sorted(matrix), "xgboost_fit": counters["fit"], "business_forecast_xgboost_predict": business_predicts, "downstream_xgboost_predict": 0, "matrix_forecast_xgboost_predict": counters["champion_predict"] - business_predicts})
    finally:
        if session:
            session.rollback()
            if cid:
                execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=cid).all()]
                vintage_ids = [row[0] for row in session.query(ForecastVintage.id).filter_by(company_id=cid).all()]
                session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).delete(synchronize_session=False)
                session.query(ForecastVintage).filter(ForecastVintage.id.in_(vintage_ids)).delete(synchronize_session=False)
                session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
                session.query(ChampionRegistryCurrent).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(ChampionRegistryTransition).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(ChampionRegistryEntry).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(ChampionChallengerDecision).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(ModelArtifact).filter_by(company_id=cid).delete(synchronize_session=False)
                for ref in storage_refs: LocalModelArtifactStorage().delete_for_controlled_cleanup(ref)
                session.query(ActualWeeklyRevision).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(ActualWeeklyObservation).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(Dataset).filter_by(company_id=cid).delete(synchronize_session=False)
                session.query(CompanyEncryptionKey).filter_by(user_id=uid).delete(synchronize_session=False)
                session.query(User).filter_by(id=uid).delete(synchronize_session=False)
                session.query(Company).filter_by(id=cid).delete(synchronize_session=False)
                session.commit()
                assert session.query(Company).filter_by(id=cid).count() == 0
            session.close()


if __name__ == "__main__":
    main()
