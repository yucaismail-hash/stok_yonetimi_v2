"""Explicit company-and-period bounded discovery of retraining candidates.

The scanner discovers existing evaluation evidence and hands Tier-3 results to
the durable B1 job boundary.  It neither creates runtime work nor acquires B4
resource leases; an operator/future controlled scheduler must do that later.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

from app.application.retraining_admission import RetrainingAdmissionService
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.application.retraining_jobs import RetrainingJobRequest, RetrainingJobService
from app.application.retraining_execution import RetrainingExecutionService
from app.database import SessionLocal
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


SCANNER_CONTRACT_VERSION = "retraining_scanner_discovery_v1"


@dataclass(frozen=True)
class RetrainingScanScope:
    company_id: object
    material_code: str
    demand_type: str
    tier: str
    candidate_fingerprint: str | None
    job_id: object | None
    job_outcome: str | None
    cooldown_status: str | None
    cooldown_until: object | None
    priority_score: object | None


@dataclass(frozen=True)
class RetrainingScanError:
    material_code: str
    demand_type: str
    code: str
    message: str


@dataclass(frozen=True)
class RetrainingScanReport:
    contract_version: str
    company_id: object
    start_period: str
    end_period: str
    scan_started_at: datetime
    scan_completed_at: datetime
    duration_ms: float
    scopes_evaluated: int
    tier0_count: int
    tier1_count: int
    tier2_count: int
    tier3_count: int
    jobs_created: int
    jobs_existing: int
    jobs_deferred: int
    scopes: tuple[RetrainingScanScope, ...]
    errors: tuple[RetrainingScanError, ...]


@dataclass(frozen=True)
class RetrainingActivationScope:
    job_id: object
    candidate_fingerprint: str
    material_code: str
    demand_type: str
    priority_score: object | None
    admission_status: str
    admission_reason_code: str | None
    runtime_execution_id: object | None
    runtime_task_id: object | None


@dataclass(frozen=True)
class RetrainingActivationReport:
    scan_report: RetrainingScanReport
    activated: tuple[RetrainingActivationScope, ...]
    errors: tuple[RetrainingScanError, ...]


class RetrainingScannerService:
    """Callable discovery only; there is deliberately no timer or global scan."""

    def __init__(self, session_factory=SessionLocal, eligibility_service_factory=RetrainingEligibilityService,
                 job_service_factory=RetrainingJobService, admission_service_factory=RetrainingAdmissionService,
                 execution_service_factory=RetrainingExecutionService, cooldown_seconds=None, capacity=None):
        self._session_factory = session_factory
        self._eligibility_service_factory = eligibility_service_factory
        self._job_service_factory = job_service_factory
        self._admission_service_factory = admission_service_factory
        self._execution_service_factory = execution_service_factory
        self._cooldown_seconds = cooldown_seconds
        self._capacity = capacity

    def scan(self, company_id, start_period, end_period, material_codes=None, demand_type=None,
             last_seen_evaluation_ids=None) -> RetrainingScanReport:
        """Discover one company's bounded scopes and accept Tier-3 candidates.

        ``last_seen_evaluation_ids`` is optional caller-owned watermark input,
        keyed by ``(material_code, demand_type)``.  The scanner persists no
        watermark of its own.
        """
        started = datetime.now(timezone.utc)
        clock = perf_counter()
        start = parse_weekly_period(start_period).period
        end = parse_weekly_period(end_period).period
        if start > end:
            raise ValueError("scan start_period must not be after end_period")
        material_set = set(material_codes) if material_codes is not None else None
        normalized_demand = validate_demand_type(demand_type) if demand_type is not None else None
        watermark_map = last_seen_evaluation_ids or {}
        scopes, errors = [], []
        tier_counts = {"TIER_0_SKIP": 0, "TIER_1_EVALUATE": 0, "TIER_2_ANALYZE": 0, "TIER_3_DEEP_LEARN_RETRAIN": 0}
        jobs_created = jobs_existing = jobs_deferred = 0
        for material, demand in self._discovered_scopes(company_id, start, end, material_set, normalized_demand):
            try:
                session = self._session_factory()
                try:
                    eligibility = self._eligibility_service_factory(session).evaluate(
                        company_id, demand, start, end, watermark_map.get((material, demand)),
                    )
                finally:
                    session.close()
                result = next((row for row in eligibility if row.material_code == material), None)
                if result is None:
                    raise ValueError("RETRAINING_ELIGIBILITY_SCOPE_UNAVAILABLE")
                tier_counts[result.tier] += 1
                if result.tier != "TIER_3_DEEP_LEARN_RETRAIN":
                    scopes.append(RetrainingScanScope(company_id, material, demand, result.tier, None, None, None, None, None, None))
                    continue
                acceptance = self._job_service_factory(self._session_factory).accept_candidate(RetrainingJobRequest(
                    company_id, material, demand, start, end, self._training_cutoff(company_id, material, demand, start, end), result,
                ))
                if acceptance.status == "CREATED":
                    jobs_created += 1
                elif acceptance.status == "ALREADY_EXISTS":
                    jobs_existing += 1
                else:
                    raise ValueError("RETRAINING_JOB_ACCEPTANCE_UNEXPECTED:" + acceptance.status)
                # B4 persists visibility only; `evaluate` never obtains a lease.
                admission = self._admission_service_factory(
                    self._session_factory, cooldown_seconds=self._cooldown_seconds,
                ).evaluate(company_id, acceptance.job_id)
                if admission.status == "COOLDOWN":
                    jobs_deferred += 1
                scopes.append(RetrainingScanScope(
                    company_id, material, demand, result.tier, acceptance.candidate_fingerprint,
                    acceptance.job_id, acceptance.status, admission.status, admission.cooldown_until,
                    admission.priority_score,
                ))
            except Exception as exc:
                errors.append(RetrainingScanError(material, demand, type(exc).__name__, str(exc)))
        completed = datetime.now(timezone.utc)
        return RetrainingScanReport(
            SCANNER_CONTRACT_VERSION, company_id, start, end, started, completed, (perf_counter() - clock) * 1000,
            sum(tier_counts.values()), tier_counts["TIER_0_SKIP"], tier_counts["TIER_1_EVALUATE"],
            tier_counts["TIER_2_ANALYZE"], tier_counts["TIER_3_DEEP_LEARN_RETRAIN"], jobs_created, jobs_existing,
            jobs_deferred, tuple(scopes), tuple(errors),
        )

    def scan_and_activate(self, company_id, start_period, end_period, *, worker_id="retraining_scanner_activation",
                          material_codes=None, demand_type=None, last_seen_evaluation_ids=None) -> RetrainingActivationReport:
        """Explicit activation bridge; discovery itself remains read-only for runtime.

        Admission ownership begins with B2's ``start`` call.  The resulting
        durable B4 lease is then used by the B2/B3 worker and released on its
        terminal outcome; this caller never owns process-local capacity.
        """
        report = self.scan(company_id, start_period, end_period, material_codes, demand_type, last_seen_evaluation_ids)
        tier3 = [scope for scope in report.scopes if scope.tier == "TIER_3_DEEP_LEARN_RETRAIN" and scope.job_id is not None]
        admission = self._admission_service_factory(self._session_factory, cooldown_seconds=self._cooldown_seconds,
                                                    **({"capacity": self._capacity} if self._capacity is not None else {}))
        # B4 owns the only priority calculation and deterministic tie-breaks.
        ranked = admission.ranked(company_id, [scope.job_id for scope in tier3]) if tier3 else []
        metadata = {scope.job_id: scope for scope in tier3}
        activated, errors = [], []
        for rank in ranked:
            scope = metadata[rank.job_id]
            try:
                execution = self._execution_service_factory(
                    self._session_factory, cooldown_seconds=self._cooldown_seconds,
                    **({"capacity": self._capacity} if self._capacity is not None else {}),
                ).start(company_id, scope.job_id, worker_id)
                activated.append(RetrainingActivationScope(
                    scope.job_id, scope.candidate_fingerprint, scope.material_code, scope.demand_type,
                    rank.priority_score, execution.status, None, execution.runtime_execution_id, execution.runtime_task_id,
                ))
            except Exception as exc:
                errors.append(RetrainingScanError(scope.material_code, scope.demand_type, type(exc).__name__, str(exc)))
        return RetrainingActivationReport(report, tuple(activated), tuple(errors))

    def _discovered_scopes(self, company_id, start, end, material_set, demand_type):
        session = self._session_factory()
        try:
            query = session.query(ForecastEvaluationPoint.material_code, ForecastEvaluation.demand_type).join(
                ForecastEvaluation, ForecastEvaluationPoint.evaluation_id == ForecastEvaluation.id,
            ).filter(
                ForecastEvaluation.company_id == company_id,
                ForecastEvaluationPoint.target_period >= start,
                ForecastEvaluationPoint.target_period <= end,
            )
            if material_set is not None:
                query = query.filter(ForecastEvaluationPoint.material_code.in_(material_set))
            if demand_type is not None:
                query = query.filter(ForecastEvaluation.demand_type == demand_type)
            return tuple(sorted(set(query.all()), key=lambda row: (row[1], row[0])))
        finally:
            session.close()

    def _training_cutoff(self, company_id, material_code, demand_type, start, end):
        session = self._session_factory()
        try:
            point = session.query(ForecastEvaluationPoint).join(
                ForecastEvaluation, ForecastEvaluationPoint.evaluation_id == ForecastEvaluation.id,
            ).filter(
                ForecastEvaluation.company_id == company_id,
                ForecastEvaluation.demand_type == demand_type,
                ForecastEvaluationPoint.material_code == material_code,
                ForecastEvaluationPoint.target_period >= start,
                ForecastEvaluationPoint.target_period <= end,
            ).order_by(ForecastEvaluationPoint.target_period.desc(), ForecastEvaluationPoint.id.desc()).first()
            if point is None or not point.input_cutoff_period:
                raise ValueError("RETRAINING_TRAINING_CUTOFF_UNAVAILABLE")
            return parse_weekly_period(point.input_cutoff_period).period
        finally:
            session.close()
