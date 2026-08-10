"""Read-only performance history and future Learning evidence from evaluations."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.application.forecast_evaluation_service import EvaluationMetrics, ForecastEvaluationService
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


PERFORMANCE_EVIDENCE_CONTRACT_VERSION = "1.0.0"
_DIMENSIONS = {"company", "product_level", "product_group", "product_class", "material_code"}


@dataclass(frozen=True)
class ForecastPerformanceHistoryRow:
    company_id: UUID
    bucket: str
    period: str
    demand_type: str
    dimension_scope: str
    dimension_value: Optional[str]
    sample_count: int
    evaluated_period_count: int
    first_evaluated_period: str
    last_evaluated_period: str
    wape: Optional[Decimal]
    wape_unavailable_reason: Optional[str]
    total_signed_error: Decimal
    mean_signed_error: Optional[Decimal]
    mae: Optional[Decimal]
    rmse: Optional[Decimal]
    smape: Optional[Decimal]
    forecast_accuracy: Optional[Decimal]
    learning_score_at_run: Optional[Decimal]
    learning_scores_at_run: tuple[Decimal, ...]
    source_evaluation_ids: tuple[UUID, ...]
    metric_contract_versions: tuple[str, ...]
    evidence_contract_version: str


class ForecastPerformanceHistoryService:
    """Materializes no state; Forecast Evaluation remains the sole source authority."""

    def __init__(self, session):
        self.session = session

    def weekly_history(self, company_id: UUID, demand_type: str, start_period: str, end_period: str, dimension_scope="company", dimension_value=None) -> tuple[ForecastPerformanceHistoryRow, ...]:
        if dimension_scope not in _DIMENSIONS:
            raise ValueError("unsupported performance dimension_scope")
        demand_type = validate_demand_type(demand_type)
        start_period = parse_weekly_period(start_period).period
        end_period = parse_weekly_period(end_period).period
        if start_period > end_period:
            raise ValueError("start_period must not be after end_period")
        query = self.session.query(ForecastEvaluationPoint, ForecastEvaluation).join(ForecastEvaluation, ForecastEvaluationPoint.evaluation_id == ForecastEvaluation.id).filter(ForecastEvaluation.company_id == company_id, ForecastEvaluation.demand_type == demand_type, ForecastEvaluationPoint.target_period >= start_period, ForecastEvaluationPoint.target_period <= end_period)
        selected = {}
        for point, evaluation in query.all():
            key = (point.material_code, point.target_period, point.actual_observation_id, point.forecast_vintage_point_id)
            ranking = (evaluation.recalculated_at, evaluation.created_at, str(evaluation.id), str(point.id))
            if key not in selected or ranking > selected[key][0]:
                selected[key] = (ranking, point, evaluation)
        buckets = {}
        for _, point, evaluation in selected.values():
            value = self._dimension_value(point, dimension_scope)
            if dimension_value is not None and value != dimension_value:
                continue
            buckets.setdefault((point.target_period, value), []).append((point, evaluation))
        rows = []
        for (period, value), evidence in buckets.items():
            points = [point for point, _ in evidence]
            metrics = ForecastEvaluationService._metrics(points)
            scores = tuple(sorted({Decimal(point.learning_score_at_run) for point in points if point.learning_score_at_run is not None}))
            rows.append(ForecastPerformanceHistoryRow(company_id=company_id, bucket="weekly", period=period, demand_type=demand_type, dimension_scope=dimension_scope, dimension_value=value, sample_count=metrics.point_count, evaluated_period_count=1, first_evaluated_period=period, last_evaluated_period=period, **self._metric_values(metrics), learning_score_at_run=scores[0] if len(scores) == 1 else None, learning_scores_at_run=scores, source_evaluation_ids=tuple(sorted({evaluation.id for _, evaluation in evidence}, key=str)), metric_contract_versions=tuple(sorted({evaluation.metric_contract_version for _, evaluation in evidence})), evidence_contract_version=PERFORMANCE_EVIDENCE_CONTRACT_VERSION))
        return tuple(sorted(rows, key=lambda row: (row.period, "" if row.dimension_value is None else row.dimension_value)))

    @staticmethod
    def _dimension_value(point, scope):
        return None if scope == "company" else getattr(point, scope)

    @staticmethod
    def _metric_values(metrics: EvaluationMetrics):
        return dict(wape=metrics.wape, wape_unavailable_reason=metrics.wape_unavailable_reason, total_signed_error=metrics.total_signed_error, mean_signed_error=metrics.mean_signed_error, mae=metrics.mae, rmse=metrics.rmse, smape=metrics.smape, forecast_accuracy=metrics.forecast_accuracy)
