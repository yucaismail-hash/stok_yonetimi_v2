"""PostgreSQL proof for bounded, non-persistent XGBoost Challenger training."""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.analysis.forecast import DemandForecaster
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.xgboost_challenger_training import (
    TIME_ORDERED_SPLIT_POLICY_VERSION,
    XGBoostChallengerTrainingRequest,
    XGBoostChallengerTrainingService,
)
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.runtime import RuntimeResultReference, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


def _row(material_code, week, quantity, product_level="finished_good"):
    return {
        "material_code": material_code,
        "period": f"2026-W{week:02d}",
        "quantity": quantity,
        "product_level": product_level,
        "product_group": "G",
        "product_class": "C",
    }


def _counts(session, company_id):
    return {
        "actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
        "revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
        "vintages": session.query(ForecastVintage).filter_by(company_id=company_id).count(),
        "evaluations": session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
        "runtime_results": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
        "runtime_attempts": session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
    }


def _signature(result):
    return (
        result.training_target_periods,
        result.validation_target_periods,
        tuple((p.target_period, p.actual, p.predicted, p.error) for p in result.validation_predictions),
        result.metrics,
    )


def _request(company_id, material_code, demand_type="sales", evidence=None):
    return XGBoostChallengerTrainingRequest(
        company_id=company_id,
        material_code=material_code,
        demand_type=demand_type,
        training_cutoff_period="2026-W20",
        eligibility_evidence=evidence,
        seed=17,
    )


def main() -> None:
    session = SessionLocal()
    company_id = user_id = None
    try:
        token = "phase3c2b2_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=token, tax_id=token)
        user = User(id=uuid7(), company_id=company.id, email=f"{token}@x.invalid", hashed_password="x")
        session.add_all((company, user))
        session.flush()
        company_id, user_id = company.id, user.id
        dataset = Dataset(
            id=uuid7(), company_id=company_id, user_id=user_id, uploaded_by=user_id,
            dataset_hash=hashlib.sha256(token.encode()).hexdigest(), source_type=token,
            encrypted_data=EncryptionService(session).encrypt_dataset(user_id, {"items": []}),
            is_active=True,
        )
        session.add(dataset)
        session.commit()

        ledger = ActualWeeklyLedgerService()
        scenarios = (
            ("FG", "finished_good", "sales", 100),
            ("SEMI", "semi_finished_good", "sales", 200),
            ("RAW", "raw_material", "sales", 300),
            ("SHARED", "finished_good", "sales", 400),
            ("SHARED", "finished_good", "consumption", 700),
        )
        for material, level, demand_type, base in scenarios:
            ledger.ingest_dataset_actuals(
                company_id, user_id, dataset.id,
                [_row(material, week, base + week, level) for week in range(1, 21)], demand_type,
            )
        ledger.ingest_dataset_actuals(
            company_id, user_id, dataset.id,
            [_row("SHORT", week, 900 + week) for week in range(1, 13)], "sales",
        )

        session.close()
        session = SessionLocal()
        trainer = XGBoostChallengerTrainingService(session)
        import xgboost

        fit_calls = {"challenger": 0, "forecast": 0}
        original_fit = xgboost.XGBRegressor.fit
        original_forecast = DemandForecaster.forecast

        def counted_fit(model, *args, **kwargs):
            fit_calls["challenger"] += 1
            return original_fit(model, *args, **kwargs)

        def counted_forecast(model, *args, **kwargs):
            fit_calls["forecast"] += 1
            return original_forecast(model, *args, **kwargs)

        xgboost.XGBRegressor.fit = counted_fit
        DemandForecaster.forecast = counted_forecast
        try:
            before_training = _counts(session, company_id)
            first = trainer.train(_request(company_id, "FG"))
            second = trainer.train(_request(company_id, "FG"))
            assert first.status == second.status == "TRAINED"
            assert first.split_policy_version == TIME_ORDERED_SPLIT_POLICY_VERSION
            assert first.training_count == 8 and first.validation_count == 4
            assert first.training_target_periods[-1] < first.validation_target_periods[0]
            assert first.parameters["random_state"] == 17
            assert first.metrics and all(
                value is not None
                for value in (first.metrics.wape, first.metrics.bias, first.metrics.mae, first.metrics.rmse)
            )
            assert all(
                point.error == point.actual - point.predicted
                and point.absolute_error == abs(point.error)
                and point.squared_error == point.error ** 2
                for point in first.validation_predictions
            )
            assert _signature(first) == _signature(second)
            assert _counts(session, company_id) == before_training

            # Accepted future evidence must not affect a fixed historical cutoff.
            ledger.ingest_dataset_actuals(
                company_id, user_id, dataset.id,
                [_row("FG", week, 1000 + week) for week in range(21, 25)], "sales",
            )
            before_cutoff_repeat = _counts(session, company_id)
            after_future = trainer.train(_request(company_id, "FG"))
            assert _signature(after_future) == _signature(first)
            assert _counts(session, company_id) == before_cutoff_repeat

            tier_three = trainer.train(_request(company_id, "RAW", evidence={"tier": "TIER_3_DEEP_LEARN_RETRAIN"}))
            before_rejected = fit_calls["challenger"]
            rejected = tuple(
                trainer.train(_request(company_id, "FG", evidence={"tier": tier}))
                for tier in ("TIER_0_SKIP", "TIER_1_EVALUATE", "TIER_2_ANALYZE")
            )
            insufficient = trainer.train(_request(company_id, "SHORT"))
            assert tier_three.status == "TRAINED"
            assert all(result.status == "NOT_ELIGIBLE" and result.reason_code == "NOT_ELIGIBLE" for result in rejected)
            assert insufficient.status == "NOT_TRAINABLE" and insufficient.reason_code == "INSUFFICIENT_TRAINING_HISTORY"
            assert fit_calls["challenger"] == before_rejected

            semi = trainer.train(_request(company_id, "SEMI"))
            raw = trainer.train(_request(company_id, "RAW"))
            shared_sales = trainer.train(_request(company_id, "SHARED", "sales"))
            shared_consumption = trainer.train(_request(company_id, "SHARED", "consumption"))
            assert semi.status == raw.status == shared_sales.status == shared_consumption.status == "TRAINED"
            assert shared_sales.validation_predictions != shared_consumption.validation_predictions
            assert fit_calls["challenger"] == 8
            assert fit_calls["forecast"] == 0
        finally:
            xgboost.XGBRegressor.fit = original_fit
            DemandForecaster.forecast = original_forecast

        print(
            "PHASE3C2B2 PASS",
            {
                "xgboost": xgboost.__version__,
                "challenger_fit_calls": fit_calls["challenger"],
                "forecast_calls": fit_calls["forecast"],
                "validation_rows": first.validation_count,
                "split_policy": first.split_policy_version,
            },
        )
    finally:
        if company_id:
            session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
            session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
            session.query(Dataset).filter_by(company_id=company_id).delete(synchronize_session=False)
            session.query(CompanyEncryptionKey).filter_by(user_id=user_id).delete(synchronize_session=False)
            session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
            session.query(Company).filter_by(id=company_id).delete(synchronize_session=False)
            session.commit()
            assert session.query(Company).filter_by(id=company_id).count() == 0
            assert session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count() == 0
        session.close()


if __name__ == "__main__":
    main()
