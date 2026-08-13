"""Callable, evidence-routed refresh orchestration for Learning projections."""
from dataclasses import dataclass
from time import perf_counter

from app.application.company_learning_refresh import CompanyLearningRefreshService
from app.application.pattern_learning_refresh import PatternLearningRefreshService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryTransition
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.learning_evidence import LearningEvidence
from app.models.retraining_job import RetrainingJob
from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision
from app.application.supplier_learning_refresh import SupplierLearningRefreshService


class LearningRefreshRoutingError(ValueError):
    """A durable evidence row cannot safely authorize the requested route."""


class LearningEvidenceNotFound(LookupError):
    pass


class LearningEvidenceTenantViolation(PermissionError):
    pass


@dataclass(frozen=True)
class LearningRefreshOrchestrationResult:
    learning_evidence_id: object
    company_id: object
    event_type: str
    material_code: str | None
    demand_type: str | None
    pattern_status: str | None
    company_status: str | None
    pattern_memory_id: object | None
    company_memory_id: object | None
    duration_ms: float
    supplier_status: str | None = None
    supplier_memory_id: object | None = None
    failure_stage: str | None = None
    failure_code: str | None = None

    @property
    def outcome(self):
        return "FAILED" if self.failure_stage else "COMPLETED"


@dataclass(frozen=True)
class _Route:
    evidence_id: object
    company_id: object
    event_type: str
    material_code: str | None
    demand_type: str | None
    pattern_cutoff_period: str | None
    supplier_id: object | None = None
    supplier_cutoff_date: object | None = None

    @property
    def refreshes_pattern(self):
        return self.pattern_cutoff_period is not None

    @property
    def refreshes_supplier(self):
        return self.supplier_id is not None


class LearningRefreshOrchestrator:
    """Routes one persisted LearningEvidence item; it never discovers dirty work."""

    _ACTUAL_EVENTS = {"ACTUAL_ACCEPTED", "ACTUAL_CORRECTED"}
    _SUPPLIER_EVENTS = {"SUPPLIER_DELIVERY_OBSERVED", "SUPPLIER_DELIVERY_CORRECTED"}
    _COMPANY_ONLY_EVENTS = {
        "FORECAST_EVALUATED", "CHAMPION_PROMOTED", "CHAMPION_ROLLED_BACK", "RETRAINING_COMPLETED",
    }

    def __init__(self, session_factory=SessionLocal, *, pattern_refresh_service=None,
                 company_refresh_service=None, before_pattern_refresh=None,
                 before_company_refresh=None, supplier_refresh_service=None, before_supplier_refresh=None):
        self._session_factory = session_factory
        self._pattern_refresh = pattern_refresh_service or PatternLearningRefreshService()
        self._company_refresh = company_refresh_service or CompanyLearningRefreshService()
        self._before_pattern = before_pattern_refresh
        self._before_company = before_company_refresh
        self._supplier_refresh = supplier_refresh_service or SupplierLearningRefreshService()
        self._before_supplier = before_supplier_refresh

    def orchestrate(self, company_id, learning_evidence_id):
        """Refresh exactly the projections authorized by one immutable evidence row."""
        started = perf_counter()
        route = self._load_and_validate(company_id, learning_evidence_id)
        pattern = company = supplier = None
        stage = None
        try:
            if route.refreshes_pattern:
                stage = "BEFORE_PATTERN_REFRESH"
                if self._before_pattern:
                    self._before_pattern(route)
                stage = "PATTERN_REFRESH"
                pattern = self._pattern_refresh.refresh(
                    route.company_id, route.material_code, route.demand_type, route.pattern_cutoff_period,
                )
            if route.refreshes_supplier:
                stage = "BEFORE_SUPPLIER_REFRESH"
                if self._before_supplier:
                    self._before_supplier(route)
                stage = "SUPPLIER_REFRESH"
                supplier = self._supplier_refresh.refresh(route.company_id, route.supplier_id,
                    route.material_code, route.supplier_cutoff_date)
                # Supplier delivery evidence intentionally does not alter Company
                # Learning until a separately versioned company policy consumes it.
                return self._result(route, pattern, company, started, supplier=supplier)
            stage = "BEFORE_COMPANY_REFRESH"
            if self._before_company:
                self._before_company(route)
            stage = "COMPANY_REFRESH"
            company = self._company_refresh.refresh(route.company_id, source_change_type=route.event_type)
            return self._result(route, pattern, company, started, supplier=supplier)
        except Exception as exc:
            return self._result(route, pattern, company, started, stage, type(exc).__name__, supplier)

    def _load_and_validate(self, company_id, learning_evidence_id):
        session = self._session_factory()
        try:
            evidence = session.query(LearningEvidence).filter_by(id=learning_evidence_id).one_or_none()
            if evidence is None:
                raise LearningEvidenceNotFound("LEARNING_EVIDENCE_NOT_FOUND")
            if evidence.company_id != company_id:
                raise LearningEvidenceTenantViolation("LEARNING_EVIDENCE_TENANT_MISMATCH")
            if evidence.event_type in self._ACTUAL_EVENTS:
                return self._actual_route(session, evidence)
            if evidence.event_type in self._SUPPLIER_EVENTS:
                return self._supplier_route(session, evidence)
            if evidence.event_type == "FORECAST_EVALUATED":
                self._forecast_route(session, evidence)
            elif evidence.event_type in {"CHAMPION_PROMOTED", "CHAMPION_ROLLED_BACK"}:
                self._champion_route(session, evidence)
            elif evidence.event_type == "RETRAINING_COMPLETED":
                self._retraining_route(session, evidence)
            else:
                raise LearningRefreshRoutingError("LEARNING_EVIDENCE_EVENT_UNSUPPORTED")
            return _Route(evidence.id, evidence.company_id, evidence.event_type,
                          evidence.material_code, evidence.demand_type, None)
        finally:
            session.close()

    @staticmethod
    def _scope_matches(evidence, source, *, start=None, end=None):
        return (
            source is not None and source.company_id == evidence.company_id
            and source.material_code == evidence.material_code
            and source.demand_type == evidence.demand_type
            and (start is None or source.period == start)
            and (end is None or source.period == end)
        )

    def _actual_route(self, session, evidence):
        if evidence.source_entity_type != "actual_weekly_observation" or not evidence.material_code or not evidence.demand_type:
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        actual = session.query(ActualWeeklyObservation).filter_by(
            id=evidence.source_entity_id, company_id=evidence.company_id,
        ).one_or_none()
        if not self._scope_matches(evidence, actual, start=evidence.affected_start_period, end=evidence.affected_end_period):
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        if evidence.event_type == "ACTUAL_CORRECTED":
            revision_id = (evidence.evidence_payload or {}).get("revision_id")
            revision = session.query(ActualWeeklyRevision).filter_by(id=revision_id, company_id=evidence.company_id).one_or_none()
            if (revision is None or revision.observation_id != actual.id or revision.change_type != "correction"
                    or revision.approval_status != "accepted"):
                raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        latest = session.query(ActualWeeklyObservation.period).filter_by(
            company_id=evidence.company_id, material_code=evidence.material_code, demand_type=evidence.demand_type,
        ).order_by(ActualWeeklyObservation.period.desc()).first()
        if latest is None:
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        return _Route(evidence.id, evidence.company_id, evidence.event_type,
                      evidence.material_code, evidence.demand_type, latest[0])

    @staticmethod
    def _supplier_route(session, evidence):
        if evidence.source_entity_type != "supplier_delivery_observation" or not evidence.material_code:
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        source = session.query(SupplierDeliveryObservation).filter_by(
            id=evidence.source_entity_id, company_id=evidence.company_id).one_or_none()
        payload = evidence.evidence_payload or {}
        if (source is None or str(source.supplier_id) != payload.get("supplier_id")
                or source.material_code != evidence.material_code):
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        if evidence.event_type == "SUPPLIER_DELIVERY_CORRECTED":
            revision = session.query(SupplierDeliveryObservationRevision).filter_by(
                id=payload.get("revision_id"), company_id=evidence.company_id).one_or_none()
            if revision is None or revision.observation_id != source.id or revision.approval_status != "accepted":
                raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        latest = session.query(SupplierDeliveryObservation.actual_receipt_date).filter_by(
            company_id=evidence.company_id, supplier_id=source.supplier_id, material_code=source.material_code,
        ).order_by(SupplierDeliveryObservation.actual_receipt_date.desc(), SupplierDeliveryObservation.id.desc()).first()
        if latest is None:
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")
        return _Route(evidence.id, evidence.company_id, evidence.event_type, source.material_code,
                      None, None, source.supplier_id, latest[0])

    @staticmethod
    def _forecast_route(session, evidence):
        source = session.query(ForecastEvaluation).filter_by(
            id=evidence.source_entity_id, company_id=evidence.company_id,
        ).one_or_none()
        if (evidence.source_entity_type != "forecast_evaluation" or source is None
                or source.demand_type != evidence.demand_type
                or source.start_period != evidence.affected_start_period
                or source.end_period != evidence.affected_end_period):
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")

    @staticmethod
    def _champion_route(session, evidence):
        source = session.query(ChampionRegistryTransition).filter_by(
            id=evidence.source_entity_id, company_id=evidence.company_id,
        ).one_or_none()
        expected = "PROMOTION" if evidence.event_type == "CHAMPION_PROMOTED" else "ROLLBACK"
        if (evidence.source_entity_type != "champion_registry_transition" or source is None
                or source.transition_type != expected
                or not LearningRefreshOrchestrator._scope_matches(evidence, source)):
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")

    @staticmethod
    def _retraining_route(session, evidence):
        source = session.query(RetrainingJob).filter_by(
            id=evidence.source_entity_id, company_id=evidence.company_id,
        ).one_or_none()
        if (evidence.source_entity_type != "retraining_job" or source is None
                or source.state not in {"trained", "not_trainable", "failed"}
                or source.material_code != evidence.material_code
                or source.demand_type != evidence.demand_type
                or source.evaluation_start_period != evidence.affected_start_period
                or source.evaluation_end_period != evidence.affected_end_period):
            raise LearningRefreshRoutingError("LEARNING_EVIDENCE_SOURCE_SCOPE_MISMATCH")

    @staticmethod
    def _result(route, pattern, company, started, failure_stage=None, failure_code=None, supplier=None):
        return LearningRefreshOrchestrationResult(
            route.evidence_id, route.company_id, route.event_type, route.material_code, route.demand_type,
            pattern.status if pattern else None, company.status if company else None,
            pattern.memory_id if pattern else None, company.memory_id if company else None,
            (perf_counter() - started) * 1000, supplier.status if supplier else None,
            supplier.memory_id if supplier else None, failure_stage, failure_code,
        )
