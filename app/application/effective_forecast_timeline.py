"""Deterministic, read-only effective Forecast Timeline derivation."""
from dataclasses import dataclass
from datetime import datetime, time, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


class EffectiveForecastTimelineError(ValueError):
    """Raised when persisted vintage evidence cannot safely form a timeline."""


def target_period_start(period: str) -> datetime:
    """Return the UTC start of a canonical ISO week without naive week arithmetic."""
    parsed = parse_weekly_period(period)
    return datetime.combine(
        datetime.fromisocalendar(parsed.year, parsed.week, 1).date(),
        time.min,
        tzinfo=timezone.utc,
    )


@dataclass(frozen=True)
class EffectiveForecastTimelineRow:
    material_code: str
    target_period: str
    forecast_value: Decimal
    forecast_vintage_id: UUID
    forecast_vintage_point_id: UUID
    runtime_result_reference_id: UUID
    forecast_available_at: datetime
    input_cutoff_period: str
    model_used: Optional[str]
    lower_interval: Optional[Decimal]
    upper_interval: Optional[Decimal]
    product_level: str
    product_group: Optional[str]
    product_class: Optional[str]
    demand_type: str
    learning_score_at_run: Optional[Decimal]


class EffectiveForecastTimelineService:
    """Resolve the latest forecast genuinely available before each target week."""

    def __init__(self, session):
        self.session = session

    def resolve(
        self,
        company_id: UUID,
        demand_type: str,
        start_period: str,
        end_period: str,
        material_code: Optional[str] = None,
    ) -> tuple[EffectiveForecastTimelineRow, ...]:
        demand_type = validate_demand_type(demand_type)
        start_period = parse_weekly_period(start_period).period
        end_period = parse_weekly_period(end_period).period
        if target_period_start(start_period) > target_period_start(end_period):
            raise EffectiveForecastTimelineError("start_period must not be after end_period")

        query = (
            self.session.query(ForecastVintagePoint, ForecastVintage)
            .join(ForecastVintage, ForecastVintagePoint.forecast_vintage_id == ForecastVintage.id)
            .filter(
                ForecastVintage.company_id == company_id,
                ForecastVintage.demand_type == demand_type,
                ForecastVintagePoint.target_period >= start_period,
                ForecastVintagePoint.target_period <= end_period,
            )
        )
        if material_code is not None:
            query = query.filter(ForecastVintagePoint.material_code == material_code)

        candidates = query.all()
        selected = {}
        for point, vintage in candidates:
            target_start = target_period_start(point.target_period)
            cutoff_start = target_period_start(vintage.input_cutoff_period)
            if cutoff_start >= target_start:
                raise EffectiveForecastTimelineError(
                    "forecast vintage input_cutoff_period must precede every target_period"
                )
            available_at = vintage.forecast_available_at
            if available_at.tzinfo is None:
                raise EffectiveForecastTimelineError("forecast_available_at must be timezone-aware")
            if available_at >= target_start:
                continue
            key = (point.material_code, point.target_period)
            ranking = (available_at, vintage.created_at, str(vintage.id), str(point.id))
            previous = selected.get(key)
            if previous is None or ranking > previous[0]:
                selected[key] = (ranking, point, vintage)

        rows = [self._row(point, vintage) for _, point, vintage in selected.values()]
        return tuple(sorted(rows, key=lambda row: (row.target_period, row.material_code, str(row.forecast_vintage_point_id))))

    @staticmethod
    def _row(point: ForecastVintagePoint, vintage: ForecastVintage) -> EffectiveForecastTimelineRow:
        return EffectiveForecastTimelineRow(
            material_code=point.material_code,
            target_period=point.target_period,
            forecast_value=point.forecast_value,
            forecast_vintage_id=vintage.id,
            forecast_vintage_point_id=point.id,
            runtime_result_reference_id=vintage.runtime_result_reference_id,
            forecast_available_at=vintage.forecast_available_at,
            input_cutoff_period=vintage.input_cutoff_period,
            model_used=point.model_used,
            lower_interval=point.lower_interval,
            upper_interval=point.upper_interval,
            product_level=point.product_level,
            product_group=point.product_group,
            product_class=point.product_class,
            demand_type=vintage.demand_type,
            learning_score_at_run=vintage.learning_score_at_run,
        )
