"""Minimal PostgreSQL cutoff-leakage proof for XGBoost weekly features."""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.xgboost_weekly_features import (
    FEATURE_SCHEMA_VERSION,
    XGBoostWeeklyFeatureBuilder,
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


def _weekly_row(
    week: int, quantity: int, material_code: str = "SKU", product_level: str = "finished_good"
) -> dict[str, object]:
    return {
        "material_code": material_code,
        "period": f"2026-W{week:02d}",
        "quantity": quantity,
        "product_level": product_level,
        "product_group": "G",
        "product_class": "C",
    }


def _period_row(
    material_code: str, period: str, quantity: int, product_level: str
) -> dict[str, object]:
    row = _weekly_row(1, quantity, material_code, product_level)
    row["period"] = period
    return row


def _matrix_signature(matrix):
    return (
        matrix.feature_names,
        matrix.X,
        matrix.y,
        matrix.target_periods,
        matrix.source_actual_observation_ids,
    )


def _build_deterministically(builder, company_id, material_code, demand_type, cutoff):
    first = builder.build(company_id, material_code, demand_type, cutoff)
    second = builder.build(company_id, material_code, demand_type, cutoff)
    assert _matrix_signature(first) == _matrix_signature(second)
    return first


def _read_only_counts(session, company_id):
    return {
        "actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
        "revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
        "vintages": session.query(ForecastVintage).filter_by(company_id=company_id).count(),
        "evaluations": session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
        "runtime_results": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
        "runtime_attempts": session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
    }


def main() -> None:
    session = SessionLocal()
    company_id = user_id = None
    try:
        token = "phase3c2b1_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=token, tax_id=token)
        user = User(
            id=uuid7(), company_id=company.id, email=f"{token}@x.invalid", hashed_password="x"
        )
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
        # W01-W20 is the only evidence available to the baseline build.
        ledger.ingest_dataset_actuals(
            company_id, user_id, dataset.id,
            [_weekly_row(week, 100 + week) for week in range(1, 21)], "sales",
        )

        session.close()
        session = SessionLocal()
        builder = XGBoostWeeklyFeatureBuilder(session)
        before_baseline = _read_only_counts(session, company_id)
        baseline = builder.build(company_id, "SKU", "sales", "2026-W20")
        after_baseline = _read_only_counts(session, company_id)

        assert baseline.feature_schema_version == FEATURE_SCHEMA_VERSION
        assert len(baseline.X) == 12  # W09-W20; earlier targets lack eight prior observations.
        assert baseline.target_periods[0] == "2026-W09"
        assert baseline.X[0][0] == 108  # lag_1 for W09 is W08.
        assert baseline.y[0] == 109  # W09 quantity is the target, not a predictor.
        assert after_baseline == before_baseline

        # Add accepted evidence only after the cutoff, then rebuild with that unchanged cutoff.
        ledger.ingest_dataset_actuals(
            company_id, user_id, dataset.id,
            [_weekly_row(week, 100 + week) for week in range(21, 25)], "sales",
        )
        before_rebuild = _read_only_counts(session, company_id)
        rebuilt = builder.build(company_id, "SKU", "sales", "2026-W20")
        after_rebuild = _read_only_counts(session, company_id)

        assert (
            baseline.X,
            baseline.y,
            baseline.target_periods,
            baseline.source_actual_observation_ids,
        ) == (
            rebuilt.X,
            rebuilt.y,
            rebuilt.target_periods,
            rebuilt.source_actual_observation_ids,
        )
        assert before_rebuild["actuals"] == 24
        assert after_rebuild == before_rebuild

        # Product-level matrix: each series must preserve the canonical metadata it carries.
        for material_code, product_level, base_quantity in (
            ("SKU_SEMI", "semi_finished_good", 200),
            ("SKU_RAW", "raw_material", 300),
        ):
            ledger.ingest_dataset_actuals(
                company_id,
                user_id,
                dataset.id,
                [_weekly_row(week, base_quantity + week, material_code, product_level) for week in range(1, 21)],
                "sales",
            )

        # The same material code deliberately has independent sales and consumption histories.
        ledger.ingest_dataset_actuals(
            company_id, user_id, dataset.id,
            [_weekly_row(week, 400 + week, "SKU_SHARED") for week in range(1, 21)], "sales",
        )
        ledger.ingest_dataset_actuals(
            company_id, user_id, dataset.id,
            [_weekly_row(week, 700 + week, "SKU_SHARED") for week in range(1, 21)], "consumption",
        )

        # 2020 is an ISO-W53 year. This chronology crosses W52 -> W53 -> 2021-W01.
        iso_periods = [f"2020-W{week:02d}" for week in range(45, 54)]
        iso_periods.extend(f"2021-W{week:02d}" for week in range(1, 13))
        ledger.ingest_dataset_actuals(
            company_id,
            user_id,
            dataset.id,
            [
                _period_row("SKU_W53", period, 500 + index, "finished_good")
                for index, period in enumerate(iso_periods, start=1)
            ],
            "sales",
        )

        session.expire_all()
        before_matrix_suite = _read_only_counts(session, company_id)
        finished_good = _build_deterministically(builder, company_id, "SKU", "sales", "2026-W20")
        semi_finished = _build_deterministically(builder, company_id, "SKU_SEMI", "sales", "2026-W20")
        raw_material = _build_deterministically(builder, company_id, "SKU_RAW", "sales", "2026-W20")
        shared_sales = _build_deterministically(builder, company_id, "SKU_SHARED", "sales", "2026-W20")
        shared_consumption = _build_deterministically(
            builder, company_id, "SKU_SHARED", "consumption", "2026-W20"
        )
        iso_matrix = _build_deterministically(builder, company_id, "SKU_W53", "sales", "2021-W12")
        after_matrix_suite = _read_only_counts(session, company_id)

        assert finished_good.product_level == "finished_good"
        assert semi_finished.product_level == "semi_finished_good"
        assert raw_material.product_level == "raw_material"
        assert shared_sales.source_actual_observation_ids != shared_consumption.source_actual_observation_ids
        assert shared_sales.y != shared_consumption.y
        assert iso_matrix.target_periods[0] == "2020-W53"
        assert iso_matrix.target_periods[1] == "2021-W01"
        assert iso_matrix.X[0][0] == 508  # W53 lag_1 is W52.
        assert iso_matrix.X[1][0:2] == (509, 508)  # W01 lags are W53 then W52.
        assert after_matrix_suite == before_matrix_suite

        import xgboost

        print(
            "PHASE3C2B1 PROBE-B PASS",
            {
                "xgboost": xgboost.__version__,
                "actuals_at_cutoff": 20,
                "future_actuals_added": 4,
                "matrix_rows": len(baseline.X),
                "cutoff": "2026-W20",
                "product_levels": 3,
                "demand_types": 2,
                "iso_w53": True,
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
            assert session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count() == 0
            assert session.query(Dataset).filter_by(company_id=company_id).count() == 0
        session.close()


if __name__ == "__main__":
    main()
