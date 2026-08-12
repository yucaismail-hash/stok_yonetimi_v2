"""Durable Tier-3 retraining candidate acceptance; it never trains or promotes."""

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.application.retraining_eligibility import RetrainingEligibility
from app.database import SessionLocal
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.models.retraining_job import RetrainingJob
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


RETRAINING_JOB_CONTRACT_VERSION = "1.0.0"


@dataclass(frozen=True)
class RetrainingJobRequest:
    company_id: object
    material_code: str
    demand_type: str
    evaluation_start_period: str
    evaluation_end_period: str
    training_cutoff_period: str
    eligibility: RetrainingEligibility


@dataclass(frozen=True)
class RetrainingJobAcceptance:
    status: str
    job_id: object | None
    candidate_fingerprint: str | None
    evaluation_evidence_fingerprint: str | None


def _canonical(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value) if value is not None and not isinstance(value, (str, int, float, bool, list, dict, tuple)) else value


def _digest(payload):
    return hashlib.sha256(json.dumps(payload, default=_canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class RetrainingJobService:
    """Company-scoped create-or-existing boundary for already eligible evidence."""

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def get(self, company_id, job_id):
        session = self._session_factory()
        try:
            return session.query(RetrainingJob).filter_by(id=job_id, company_id=company_id, is_deleted=False).one_or_none()
        finally:
            session.close()

    def accept_candidate(self, request: RetrainingJobRequest) -> RetrainingJobAcceptance:
        eligibility = request.eligibility
        if not self._eligible_request(request):
            return RetrainingJobAcceptance("NOT_ELIGIBLE", None, None, None)
        session = self._session_factory()
        try:
            evidence = self._evidence(session, request)
            candidate_fingerprint = _digest({
                "retraining_job_contract_version": RETRAINING_JOB_CONTRACT_VERSION,
                "company_id": request.company_id,
                "material_code": request.material_code,
                "demand_type": request.demand_type,
                "evaluation_window": [evidence["evaluation_start_period"], evidence["evaluation_end_period"]],
                "latest_evaluation_id": eligibility.latest_evaluation_id,
                "evaluation_evidence_fingerprint": evidence["evaluation_evidence_fingerprint"],
                "eligibility_contract_version": eligibility.contract_version,
                "training_cutoff_period": evidence["training_cutoff_period"],
                "eligibility": evidence["eligibility"],
            })
            existing = session.query(RetrainingJob).filter_by(company_id=request.company_id, candidate_fingerprint=candidate_fingerprint, is_deleted=False).one_or_none()
            if existing is not None:
                return RetrainingJobAcceptance("ALREADY_EXISTS", existing.id, candidate_fingerprint, evidence["evaluation_evidence_fingerprint"])
            job = RetrainingJob(
                company_id=request.company_id, material_code=request.material_code, demand_type=request.demand_type,
                runtime_execution_id=None, state="pending", eligibility_tier=eligibility.tier,
                eligibility_action=eligibility.recommended_action, eligibility_contract_version=eligibility.contract_version,
                eligibility_reason_codes=list(eligibility.reason_codes), performance_drift=eligibility.performance_drift,
                demand_drift=eligibility.demand_drift, sample_count=eligibility.sample_count,
                evaluated_period_count=eligibility.evaluated_period_count,
                evaluation_start_period=evidence["evaluation_start_period"], evaluation_end_period=evidence["evaluation_end_period"],
                latest_evaluation_id=eligibility.latest_evaluation_id, training_cutoff_period=evidence["training_cutoff_period"],
                product_level=eligibility.product_level, product_group=eligibility.product_group, product_class=eligibility.product_class,
                current_wape=eligibility.current_wape, baseline_wape=eligibility.baseline_wape,
                mean_signed_error=eligibility.mean_signed_error,
                evaluation_evidence_fingerprint=evidence["evaluation_evidence_fingerprint"], candidate_fingerprint=candidate_fingerprint,
                eligibility_evidence=evidence["eligibility"],
            )
            session.add(job)
            session.commit()
            return RetrainingJobAcceptance("CREATED", job.id, candidate_fingerprint, evidence["evaluation_evidence_fingerprint"])
        except IntegrityError:
            session.rollback()
            existing = session.query(RetrainingJob).filter_by(company_id=request.company_id, candidate_fingerprint=locals().get("candidate_fingerprint"), is_deleted=False).one_or_none()
            if existing is not None:
                return RetrainingJobAcceptance("ALREADY_EXISTS", existing.id, candidate_fingerprint, evidence["evaluation_evidence_fingerprint"])
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _eligible_request(request):
        eligibility = request.eligibility
        return (
            eligibility.company_id == request.company_id
            and eligibility.material_code == request.material_code
            and eligibility.demand_type == validate_demand_type(request.demand_type)
            and eligibility.tier == "TIER_3_DEEP_LEARN_RETRAIN"
            and eligibility.recommended_action == "RETRAIN_ELIGIBLE"
            and eligibility.latest_evaluation_id is not None
        )

    def _evidence(self, session, request):
        eligibility = request.eligibility
        demand_type = validate_demand_type(request.demand_type)
        start = parse_weekly_period(request.evaluation_start_period).period
        end = parse_weekly_period(request.evaluation_end_period).period
        cutoff = parse_weekly_period(request.training_cutoff_period).period
        points = session.query(ForecastEvaluationPoint).join(
            ForecastEvaluation, ForecastEvaluationPoint.evaluation_id == ForecastEvaluation.id
        ).filter(
            ForecastEvaluation.company_id == request.company_id,
            ForecastEvaluation.demand_type == demand_type,
            ForecastEvaluationPoint.material_code == request.material_code,
            ForecastEvaluationPoint.target_period >= start,
            ForecastEvaluationPoint.target_period <= end,
        ).order_by(ForecastEvaluationPoint.target_period, ForecastEvaluationPoint.id).all()
        if not points:
            raise ValueError("ELIGIBILITY_EVIDENCE_UNAVAILABLE")
        evaluations = session.query(ForecastEvaluation).filter(
            ForecastEvaluation.id.in_({point.evaluation_id for point in points})
        ).order_by(ForecastEvaluation.recalculated_at, ForecastEvaluation.id).all()
        if not any(row.id == eligibility.latest_evaluation_id for row in evaluations):
            raise ValueError("ELIGIBILITY_EVIDENCE_STALE")
        point_payload = [{
            "id": point.id, "evaluation_id": point.evaluation_id, "target_period": point.target_period,
            "actual_observation_id": point.actual_observation_id, "actual_revision_id": point.actual_revision_id,
            "accepted_actual_quantity": point.accepted_actual_quantity, "forecast_vintage_id": point.forecast_vintage_id,
            "forecast_vintage_point_id": point.forecast_vintage_point_id, "runtime_result_reference_id": point.runtime_result_reference_id,
            "forecast_value": point.forecast_value, "input_cutoff_period": point.input_cutoff_period,
            "product_level": point.product_level, "product_group": point.product_group, "product_class": point.product_class,
            "error": point.error, "absolute_error": point.absolute_error, "squared_error": point.squared_error,
        } for point in points]
        evaluation_payload = [{
            # Recalculation timestamp is operational metadata, not source
            # evidence. Including it would manufacture a new retraining
            # candidate after a rejected correction refresh with unchanged
            # evaluated points/metrics.
            "id": row.id, "metric_contract_version": row.metric_contract_version,
            "evaluated_point_count": row.evaluated_point_count, "wape": row.wape, "mean_signed_error": row.mean_signed_error,
            "mae": row.mae, "rmse": row.rmse, "smape": row.smape,
        } for row in evaluations]
        evaluation_evidence_fingerprint = _digest({"points": point_payload, "evaluations": evaluation_payload})
        eligibility_payload = {
            "tier": eligibility.tier, "action": eligibility.recommended_action,
            "contract_version": eligibility.contract_version, "reason_codes": list(eligibility.reason_codes),
            "sample_count": eligibility.sample_count, "evaluated_period_count": eligibility.evaluated_period_count,
            "current_wape": eligibility.current_wape, "baseline_wape": eligibility.baseline_wape,
            "mean_signed_error": eligibility.mean_signed_error, "performance_drift": eligibility.performance_drift,
            "demand_drift": eligibility.demand_drift, "latest_evaluation_id": eligibility.latest_evaluation_id,
        }
        return {
            "evaluation_start_period": start, "evaluation_end_period": end, "training_cutoff_period": cutoff,
            "evaluation_evidence_fingerprint": evaluation_evidence_fingerprint, "eligibility": json.loads(json.dumps(eligibility_payload, default=_canonical)),
        }
