"""Durable current Forecast-to-Actual evaluation using the effective timeline."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from math import sqrt
from typing import Optional
from uuid import UUID

from app.application.effective_forecast_timeline import EffectiveForecastTimelineService
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


METRIC_CONTRACT_VERSION = "1.0.0"


@dataclass(frozen=True)
class EvaluationMetrics:
    point_count: int
    wape: Optional[Decimal]
    wape_unavailable_reason: Optional[str]
    forecast_accuracy: Optional[Decimal]
    total_signed_error: Decimal
    mean_signed_error: Optional[Decimal]
    mae: Optional[Decimal]
    rmse: Optional[Decimal]
    smape: Optional[Decimal]


@dataclass(frozen=True)
class EvaluationResolution:
    evaluation: Optional[ForecastEvaluation]
    evaluated_point_count: int
    awaiting_actual: tuple[tuple[str, str], ...]
    no_eligible_forecast: tuple[tuple[str, str], ...]


class ForecastEvaluationService:
    """Writes one current evaluation identity; it never changes forecast evidence."""

    def __init__(self, session, timeline_service=None):
        self.session = session
        self.timeline_service = timeline_service or EffectiveForecastTimelineService(session)

    @staticmethod
    def _metrics(points) -> EvaluationMetrics:
        count = len(points)
        if not count:
            return EvaluationMetrics(0, None, "no_evaluation_points", None, Decimal("0"), None, None, None, None)
        actuals = [Decimal(point.accepted_actual_quantity) for point in points]
        forecasts = [Decimal(point.forecast_value) for point in points]
        errors = [actual - forecast for actual, forecast in zip(actuals, forecasts)]
        absolute_errors = [abs(error) for error in errors]
        total_actual = sum((abs(value) for value in actuals), Decimal("0"))
        total_absolute_error = sum(absolute_errors, Decimal("0"))
        total_signed_error = sum(errors, Decimal("0"))
        wape = None if total_actual == 0 else total_absolute_error / total_actual
        smape_values = [Decimal("2") * abs(error) / (abs(actual) + abs(forecast)) for actual, forecast, error in zip(actuals, forecasts, errors) if abs(actual) + abs(forecast) != 0]
        return EvaluationMetrics(
            point_count=count,
            wape=wape,
            wape_unavailable_reason="zero_actual_denominator" if wape is None else None,
            forecast_accuracy=max(Decimal("0"), Decimal("1") - wape) if wape is not None else None,
            total_signed_error=total_signed_error,
            mean_signed_error=total_signed_error / count,
            mae=total_absolute_error / count,
            rmse=Decimal(str(sqrt(float(sum((error * error for error in errors), Decimal("0")) / count)))),
            smape=sum(smape_values, Decimal("0")) / len(smape_values) if smape_values else None,
        )

    def evaluate(self, company_id: UUID, demand_type: str, start_period: str, end_period: str) -> EvaluationResolution:
        demand_type = validate_demand_type(demand_type)
        start_period = parse_weekly_period(start_period).period
        end_period = parse_weekly_period(end_period).period
        timeline = self.timeline_service.resolve(company_id, demand_type, start_period, end_period)
        actuals = self.session.query(ActualWeeklyObservation).filter_by(company_id=company_id, demand_type=demand_type).filter(ActualWeeklyObservation.period >= start_period, ActualWeeklyObservation.period <= end_period).all()
        actual_by_key = {(row.material_code, row.period): row for row in actuals}
        timeline_by_key = {(row.material_code, row.target_period): row for row in timeline}
        awaiting_actual = tuple(sorted(key for key in timeline_by_key if key not in actual_by_key))
        no_forecast = tuple(sorted(key for key in actual_by_key if key not in timeline_by_key))
        pairs = [(timeline_by_key[key], actual_by_key[key]) for key in sorted(timeline_by_key.keys() & actual_by_key.keys())]
        identity = dict(company_id=company_id, demand_type=demand_type, start_period=start_period, end_period=end_period, metric_contract_version=METRIC_CONTRACT_VERSION)
        evaluation = self.session.query(ForecastEvaluation).filter_by(**identity).one_or_none()
        if not pairs:
            if evaluation is not None:
                self.session.query(ForecastEvaluationPoint).filter_by(evaluation_id=evaluation.id).delete(synchronize_session=False)
                self.session.delete(evaluation)
                self.session.flush()
            return EvaluationResolution(None, 0, awaiting_actual, no_forecast)
        if evaluation is None:
            evaluation = ForecastEvaluation(**identity)
            self.session.add(evaluation); self.session.flush()
        existing = {(row.material_code, row.target_period): row for row in self.session.query(ForecastEvaluationPoint).filter_by(evaluation_id=evaluation.id)}
        retained = set()
        for timeline_row, actual in pairs:
            key = (timeline_row.material_code, timeline_row.target_period); retained.add(key)
            point = existing.get(key)
            values = self._point_values(evaluation.id, timeline_row, actual)
            if point is None:
                point = ForecastEvaluationPoint(**values); self.session.add(point)
            else:
                for name, value in values.items():
                    if name != "evaluation_id": setattr(point, name, value)
        for key, point in existing.items():
            if key not in retained: self.session.delete(point)
        self.session.flush()
        points = self.session.query(ForecastEvaluationPoint).filter_by(evaluation_id=evaluation.id).all()
        metrics = self._metrics(points)
        evaluation.evaluated_point_count = metrics.point_count
        evaluation.wape = metrics.wape; evaluation.wape_unavailable_reason = metrics.wape_unavailable_reason
        evaluation.forecast_accuracy = metrics.forecast_accuracy; evaluation.total_signed_error = metrics.total_signed_error
        evaluation.mean_signed_error = metrics.mean_signed_error; evaluation.mae = metrics.mae; evaluation.rmse = metrics.rmse; evaluation.smape = metrics.smape
        evaluation.recalculated_at = datetime.now(timezone.utc)
        self.session.flush()
        return EvaluationResolution(evaluation, metrics.point_count, awaiting_actual, no_forecast)

    def aggregate(self, evaluation_id: UUID, company_id: UUID, product_level=None, product_group=None, product_class=None, material_code=None) -> EvaluationMetrics:
        query = self.session.query(ForecastEvaluationPoint).join(ForecastEvaluation, ForecastEvaluationPoint.evaluation_id == ForecastEvaluation.id).filter(ForecastEvaluation.id == evaluation_id, ForecastEvaluation.company_id == company_id)
        for column, value in ((ForecastEvaluationPoint.product_level, product_level), (ForecastEvaluationPoint.product_group, product_group), (ForecastEvaluationPoint.product_class, product_class), (ForecastEvaluationPoint.material_code, material_code)):
            if value is not None: query = query.filter(column == value)
        return self._metrics(query.all())

    def _point_values(self, evaluation_id, timeline_row, actual):
        revision = self.session.query(ActualWeeklyRevision).filter_by(company_id=actual.company_id, observation_id=actual.id, approval_status="accepted").order_by(ActualWeeklyRevision.approved_at.desc(), ActualWeeklyRevision.created_at.desc(), ActualWeeklyRevision.id.desc()).first()
        error = Decimal(actual.quantity) - Decimal(timeline_row.forecast_value)
        return dict(evaluation_id=evaluation_id, material_code=timeline_row.material_code, target_period=timeline_row.target_period, actual_observation_id=actual.id, actual_revision_id=revision.id if revision else None, accepted_actual_quantity=actual.quantity, forecast_vintage_id=timeline_row.forecast_vintage_id, forecast_vintage_point_id=timeline_row.forecast_vintage_point_id, runtime_result_reference_id=timeline_row.runtime_result_reference_id, forecast_value=timeline_row.forecast_value, forecast_available_at=timeline_row.forecast_available_at, input_cutoff_period=timeline_row.input_cutoff_period, product_level=timeline_row.product_level, product_group=timeline_row.product_group, product_class=timeline_row.product_class, learning_score_at_run=timeline_row.learning_score_at_run, error=error, absolute_error=abs(error), squared_error=error * error, bias_contribution=error)
