"""Test-only real Forecast-to-Champion-evidence fixture.

The comparison window deliberately follows the current wall-clock week.  A
Forecast Vintage's real ``forecast_available_at`` is never rewritten: the
effective timeline decides eligibility exactly as production does.
"""
import hashlib
import inspect
from dataclasses import dataclass

from uuid_extensions import uuid7

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.forecast_evaluation_service import ForecastEvaluationService
from app.application.forecast_performance_history import ForecastPerformanceHistoryService
from app.application.workflow_dispatcher import WorkflowDispatcher
from app.database import SessionLocal
from app.engine.local_forecast_runner import LocalForecastRunner
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService


MATERIAL_CODE = "SKU"
DEMAND_TYPE = "sales"
# On 2026-08-11, W33 has already started.  W34-W37 are all genuinely future
# target weeks for a W32 forecast, so its unmodified availability time is valid.
INPUT_CUTOFF_PERIOD = "2026-W32"
COMPARISON_PERIODS = ("2026-W34", "2026-W35", "2026-W36", "2026-W37")


@dataclass(frozen=True)
class ChampionFixtureIds:
    company_id: object
    user_id: object
    dataset_id: object
    execution_id: object
    runtime_result_reference_id: object
    forecast_vintage_id: object
    evaluation_id: object
    material_code: str
    demand_type: str


@dataclass(frozen=True)
class ChampionEvidence:
    company_id: object
    material_code: str
    demand_type: str
    model_identity: str | None
    runtime_result_reference_ids: tuple
    forecast_vintage_ids: tuple
    evaluation_ids: tuple
    target_periods: tuple
    sample_count: int
    evaluated_period_count: int
    wape: object
    bias: object
    mae: object
    rmse: object
    product_level: str
    product_group: str | None
    product_class: str | None


def _forecast_params():
    return {
        "horizon": 5,
        "forecast_vintage": {
            "input_cutoff_period": INPUT_CUTOFF_PERIOD,
            "demand_type": DEMAND_TYPE,
            "product_metadata": {
                MATERIAL_CODE: {
                    "product_level": "finished_good",
                    "product_group": "G",
                    "product_class": "C",
                }
            },
        },
    }


async def create_finished_good_sales(before_forecast=None):
    """Persist a complete, canonical forecast/evaluation evidence chain."""
    session = SessionLocal()
    company_id = user_id = dataset_id = execution_id = None
    try:
        tag = "champion_fixture_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@x.invalid", hashed_password="x")
        session.add_all((company, user))
        session.flush()
        company_id, user_id = company.id, user.id
        dataset = Dataset(
            id=uuid7(), company_id=company_id, user_id=user_id, uploaded_by=user_id,
            dataset_hash=hashlib.sha256(tag.encode()).hexdigest(), source_type=tag,
            encrypted_data=EncryptionService(session).encrypt_dataset(user_id, {
                "items": [{"sku_code": MATERIAL_CODE, "demand_history": [100 + index for index in range(24)], "lead_time_days": 14}]
            }),
            is_active=True,
        )
        session.add(dataset)
        session.commit()
        dataset_id = dataset.id

        # This is historical source evidence available before both Challenger
        # training and Champion Forecast execution.  It is deliberately
        # separate from W34-W37 comparison actuals below.
        ActualWeeklyLedgerService().ingest_dataset_actuals(
            company_id, user_id, dataset_id,
            [{"material_code": MATERIAL_CODE, "period": f"2026-W{week:02d}", "quantity": 100 + (week % 7),
              "product_level": "finished_good", "product_group": "G", "product_class": "C"}
             for week in range(1, 33)],
            DEMAND_TYPE,
        )
        if before_forecast is not None:
            callback_result = before_forecast(company_id, user_id, dataset_id)
            if inspect.isawaitable(callback_result):
                await callback_result

        accepted = await WorkflowDispatcher().dispatch_single_analysis(
            company_id, user_id, dataset_id, "forecast", params=_forecast_params(),
        )
        execution_id = accepted["execution_id"]
        reference = await LocalForecastRunner().run(execution_id)
        if reference is None or not isinstance(reference.inline_result, dict):
            raise AssertionError("standalone Forecast did not create a validated RuntimeResultReference")

        # Actuals arrive only after the Forecast execution has completed.
        ActualWeeklyLedgerService().ingest_dataset_actuals(
            company_id, user_id, dataset_id,
            [{"material_code": MATERIAL_CODE, "period": period, "quantity": 134 + index,
              "product_level": "finished_good", "product_group": "G", "product_class": "C"}
             for index, period in enumerate(COMPARISON_PERIODS)],
            DEMAND_TYPE,
        )
        session.close()
        session = SessionLocal()
        vintage = session.query(ForecastVintage).filter_by(execution_id=execution_id).one()
        reference = session.query(RuntimeResultReference).filter_by(id=vintage.runtime_result_reference_id).one()
        points = session.query(ForecastVintagePoint).filter_by(forecast_vintage_id=vintage.id).all()
        if reference.inline_result.get("horizon") != 5 or len(points) != 5:
            raise AssertionError("Forecast result was not projected through the canonical Vintage boundary")
        resolution = ForecastEvaluationService(session).evaluate(
            company_id, DEMAND_TYPE, COMPARISON_PERIODS[0], COMPARISON_PERIODS[-1],
        )
        if resolution.evaluation is None or resolution.evaluated_point_count != len(COMPARISON_PERIODS):
            raise AssertionError("eligible Forecast/Actual evidence did not create the expected evaluation")
        session.commit()
        ids = ChampionFixtureIds(
            company_id, user_id, dataset_id, execution_id, reference.id, vintage.id,
            resolution.evaluation.id, MATERIAL_CODE, DEMAND_TYPE,
        )
        return ids, reconstruct(session, ids), tag
    except Exception:
        session.rollback()
        if company_id is not None:
            _cleanup_company(session, company_id, user_id)
        raise
    finally:
        session.close()


def reconstruct(session, ids):
    """Rebuild fixture evidence using only primitive identifiers and PostgreSQL."""
    points = session.query(ForecastEvaluationPoint).filter_by(
        evaluation_id=ids.evaluation_id, material_code=ids.material_code,
    ).order_by(ForecastEvaluationPoint.target_period).all()
    if not points:
        raise AssertionError("evaluation points are unavailable")
    metrics = ForecastEvaluationService(session).aggregate(
        ids.evaluation_id, ids.company_id, material_code=ids.material_code,
    )
    history = ForecastPerformanceHistoryService(session).weekly_history(
        ids.company_id, ids.demand_type, points[0].target_period, points[-1].target_period,
        dimension_scope="material_code", dimension_value=ids.material_code,
    )
    if len(history) != len(points):
        raise AssertionError("Forecast Performance History could not reconstruct each evaluation period")
    point = points[0]
    vintage_point = session.query(ForecastVintagePoint).filter_by(id=point.forecast_vintage_point_id).one()
    return ChampionEvidence(
        ids.company_id, ids.material_code, ids.demand_type, vintage_point.model_used,
        tuple(sorted({row.runtime_result_reference_id for row in points}, key=str)),
        tuple(sorted({row.forecast_vintage_id for row in points}, key=str)),
        tuple(sorted({ids.evaluation_id}, key=str)), tuple(row.target_period for row in points),
        metrics.point_count, len(history), metrics.wape, metrics.mean_signed_error,
        metrics.mae, metrics.rmse, point.product_level, point.product_group, point.product_class,
    )


def _cleanup_company(session, company_id, user_id):
    """Delete only dependencies owned by one known synthetic company id."""
    execution_ids = [row[0] for row in session.query(RuntimeExecution.execution_id).filter_by(company_id=company_id)]
    vintage_ids = [row[0] for row in session.query(ForecastVintage.id).filter_by(company_id=company_id)]
    evaluation_ids = [row[0] for row in session.query(ForecastEvaluation.id).filter_by(company_id=company_id)]
    if evaluation_ids:
        session.query(ForecastEvaluationPoint).filter(ForecastEvaluationPoint.evaluation_id.in_(evaluation_ids)).delete(synchronize_session=False)
        session.query(ForecastEvaluation).filter(ForecastEvaluation.id.in_(evaluation_ids)).delete(synchronize_session=False)
    if vintage_ids:
        session.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).delete(synchronize_session=False)
        session.query(ForecastVintage).filter(ForecastVintage.id.in_(vintage_ids)).delete(synchronize_session=False)
    if execution_ids:
        session.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        session.query(RuntimeTaskAttempt).filter(RuntimeTaskAttempt.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        session.query(RuntimeTask).filter(RuntimeTask.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        session.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
    session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(Dataset).filter_by(company_id=company_id).delete(synchronize_session=False)
    session.query(CompanyEncryptionKey).filter_by(user_id=user_id).delete(synchronize_session=False)
    session.query(User).filter_by(id=user_id).delete(synchronize_session=False)
    session.query(Company).filter_by(id=company_id).delete(synchronize_session=False)
    session.commit()


def cleanup(session, ids):
    _cleanup_company(session, ids.company_id, ids.user_id)
