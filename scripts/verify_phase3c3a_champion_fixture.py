"""PostgreSQL smoke proof for the real Champion evidence fixture."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.effective_forecast_timeline import EffectiveForecastTimelineService, target_period_start
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation
from app.models.company import Company
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeResultReference
from scripts.support.champion_evidence_fixture import (
    COMPARISON_PERIODS,
    create_finished_good_sales,
    cleanup,
    reconstruct,
)


async def main():
    ids = evidence = tag = None
    session = None
    try:
        ids, evidence, tag = await create_finished_good_sales()
        session = SessionLocal()
        reference = session.query(RuntimeResultReference).filter_by(id=ids.runtime_result_reference_id).one()
        vintage = session.query(ForecastVintage).filter_by(id=ids.forecast_vintage_id).one()
        vintage_points = session.query(ForecastVintagePoint).filter_by(
            forecast_vintage_id=ids.forecast_vintage_id,
        ).order_by(ForecastVintagePoint.target_period).all()
        timeline = EffectiveForecastTimelineService(session).resolve(
            ids.company_id, ids.demand_type, COMPARISON_PERIODS[0], COMPARISON_PERIODS[-1], ids.material_code,
        )
        evaluation = session.query(ForecastEvaluation).filter_by(id=ids.evaluation_id).one()
        evaluation_points = session.query(ForecastEvaluationPoint).filter_by(evaluation_id=ids.evaluation_id).all()
        actual_count = session.query(ActualWeeklyObservation).filter_by(
            company_id=ids.company_id, material_code=ids.material_code, demand_type=ids.demand_type,
        ).filter(ActualWeeklyObservation.period >= COMPARISON_PERIODS[0]).filter(
            ActualWeeklyObservation.period <= COMPARISON_PERIODS[-1]
        ).count()
        assert reference.validation_status == "validated" and reference.inline_result["horizon"] == 5
        assert vintage.input_cutoff_period == "2026-W32"
        assert [point.target_period for point in vintage_points] == ["2026-W33", *COMPARISON_PERIODS]
        assert tuple(row.target_period for row in timeline) == COMPARISON_PERIODS
        assert all(vintage.forecast_available_at < target_period_start(row.target_period) for row in timeline)
        assert actual_count == 4 and evaluation.evaluated_point_count == 4 and len(evaluation_points) == 4
        session.close()
        session = SessionLocal()
        assert reconstruct(session, ids) == evidence
        print("PHASE3C3A-F0 PASS", json.dumps({
            "runtime_reference": "validated", "cutoff": vintage.input_cutoff_period,
            "comparison_periods": evidence.target_periods, "sample_count": evidence.sample_count,
            "wape": str(evidence.wape), "fresh_session": True,
        }), flush=True)
    finally:
        if session is not None:
            if ids is not None:
                cleanup(session, ids)
                assert session.query(Company).filter_by(id=ids.company_id).count() == 0
            else:
                session.close()


if __name__ == "__main__":
    asyncio.run(main())
