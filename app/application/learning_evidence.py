"""Canonical immutable Learning Evidence writer; it never performs learning materialization."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.champion_registry import ChampionRegistryTransition
from app.models.forecast_evaluation import ForecastEvaluation, ForecastEvaluationPoint
from app.models.learning_evidence import LearningEvidence
from app.models.learning_refresh_delivery import LearningRefreshDelivery
from app.models.retraining_job import RetrainingJob
from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision
from app.models.event_observation import EventObservation, EventRevision
from app.models.company import UserMaterial


LEARNING_EVIDENCE_CONTRACT_VERSION = "learning_evidence_v1"
LEARNING_EVIDENCE_PAYLOAD_VERSION = "1.0.0"
TERMINAL_RETRAINING_STATES = {"trained", "not_trainable", "failed"}
LEARNING_REFRESH_DELIVERY_CONTRACT_VERSION = "learning_refresh_delivery_v1"


@dataclass(frozen=True)
class LearningEvidenceWriteResult:
    status: str
    evidence_id: object
    evidence_fingerprint: str


def _json_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "as_tuple"):
        return format(value, "f")
    return str(value) if value is not None and not isinstance(value, (str, int, float, bool, list, dict, tuple)) else value


def canonical_evidence_fingerprint(payload):
    """Semantic, company-scoped SHA-256 identity; never includes volatile timestamps."""
    return sha256(json.dumps(payload, default=_json_value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class LearningEvidenceService:
    """Source-specific, company-scoped create-or-existing boundary."""

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def record_actual_accepted(self, company_id, observation_id):
        return self._record(company_id, "ACTUAL_ACCEPTED", observation_id)

    def record_actual_corrected(self, company_id, revision_id):
        return self._record(company_id, "ACTUAL_CORRECTED", revision_id)

    def record_forecast_evaluated(self, company_id, evaluation_id):
        return self._record(company_id, "FORECAST_EVALUATED", evaluation_id)

    def record_champion_promotion(self, company_id, transition_id):
        return self._record(company_id, "CHAMPION_PROMOTED", transition_id)

    def record_champion_rollback(self, company_id, transition_id):
        return self._record(company_id, "CHAMPION_ROLLED_BACK", transition_id)

    def record_retraining_completed(self, company_id, job_id):
        return self._record(company_id, "RETRAINING_COMPLETED", job_id)

    def record_supplier_delivery_observed(self, company_id, observation_id):
        return self._record(company_id, "SUPPLIER_DELIVERY_OBSERVED", observation_id)

    def record_supplier_delivery_corrected(self, company_id, revision_id):
        return self._record(company_id, "SUPPLIER_DELIVERY_CORRECTED", revision_id)

    def record_event_observed(self, company_id, event_id): return self._record(company_id, "EVENT_OBSERVED", event_id)
    def record_event_corrected(self, company_id, revision_id): return self._record(company_id, "EVENT_CORRECTED", revision_id)
    def record_event_cancelled(self, company_id, revision_id): return self._record(company_id, "EVENT_CANCELLED", revision_id)

    def get(self, company_id, evidence_id):
        session = self._session_factory()
        try:
            return session.query(LearningEvidence).filter_by(company_id=company_id, id=evidence_id).one_or_none()
        finally:
            session.close()

    def list_scope(self, company_id, *, material_code=None, demand_type=None):
        session = self._session_factory()
        try:
            query = session.query(LearningEvidence).filter_by(company_id=company_id)
            if material_code is not None:
                query = query.filter_by(material_code=material_code)
            if demand_type is not None:
                query = query.filter_by(demand_type=demand_type)
            return tuple(query.order_by(LearningEvidence.recorded_at, LearningEvidence.id).all())
        finally:
            session.close()

    def lineage(self, company_id, evidence_id):
        session = self._session_factory()
        try:
            rows = []
            current = session.query(LearningEvidence).filter_by(company_id=company_id, id=evidence_id).one_or_none()
            while current is not None:
                rows.append(current)
                current = session.query(LearningEvidence).filter_by(company_id=company_id, id=current.supersedes_evidence_id).one_or_none() if current.supersedes_evidence_id else None
            return tuple(rows)
        finally:
            session.close()

    def _record(self, company_id, event_type, source_id):
        session = self._session_factory()
        try:
            specification = self._build(session, company_id, event_type, source_id)
            fingerprint = canonical_evidence_fingerprint(specification["semantic"])
            existing = session.query(LearningEvidence).filter_by(company_id=company_id, evidence_fingerprint=fingerprint).one_or_none()
            if existing is not None:
                return LearningEvidenceWriteResult("ALREADY_EXISTS", existing.id, fingerprint)
            row = LearningEvidence(
                company_id=company_id, event_type=event_type, evidence_fingerprint=fingerprint,
                contract_version=LEARNING_EVIDENCE_CONTRACT_VERSION, payload_version=LEARNING_EVIDENCE_PAYLOAD_VERSION,
                **specification["row"],
            )
            try:
                session.add(row); session.flush()
                # The immutable evidence and its delivery intent commit atomically: a
                # process crash cannot leave persisted evidence without durable work.
                session.add(LearningRefreshDelivery(
                    company_id=company_id, learning_evidence_id=row.id,
                    delivery_contract_version=LEARNING_REFRESH_DELIVERY_CONTRACT_VERSION,
                    state="pending", attempt_count=0, row_version=1,
                ))
                session.commit()
                return LearningEvidenceWriteResult("CREATED", row.id, fingerprint)
            except IntegrityError:
                session.rollback()
                existing = session.query(LearningEvidence).filter_by(company_id=company_id, evidence_fingerprint=fingerprint).one_or_none()
                if existing is None:
                    raise
                return LearningEvidenceWriteResult("ALREADY_EXISTS", existing.id, fingerprint)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _build(self, session, company_id, event_type, source_id):
        builders = {
            "ACTUAL_ACCEPTED": self._actual_accepted,
            "ACTUAL_CORRECTED": self._actual_corrected,
            "FORECAST_EVALUATED": self._forecast_evaluated,
            "CHAMPION_PROMOTED": self._champion_transition,
            "CHAMPION_ROLLED_BACK": self._champion_transition,
            "RETRAINING_COMPLETED": self._retraining_completed,
            "SUPPLIER_DELIVERY_OBSERVED": self._supplier_delivery_observed,
            "SUPPLIER_DELIVERY_CORRECTED": self._supplier_delivery_corrected,
            "EVENT_OBSERVED": self._event_observed,
            "EVENT_CORRECTED": self._event_revision,
            "EVENT_CANCELLED": self._event_revision,
        }
        if event_type not in builders:
            raise ValueError("LEARNING_EVIDENCE_EVENT_UNSUPPORTED")
        return builders[event_type](session, company_id, source_id, event_type)

    @staticmethod
    def _base(row, semantic):
        # JSONB must contain a portable reconstruction of numeric source facts;
        # semantic fingerprinting still receives the original canonical values.
        row = dict(row)
        row["evidence_payload"] = json.loads(json.dumps(row["evidence_payload"], default=_json_value, sort_keys=True))
        return {"row": row, "semantic": {"contract_version": LEARNING_EVIDENCE_CONTRACT_VERSION, **semantic}}

    def _actual_accepted(self, session, company_id, source_id, event_type):
        source = session.query(ActualWeeklyObservation).filter_by(id=source_id, company_id=company_id).one_or_none()
        if source is None:
            raise LookupError("ACTUAL_OBSERVATION_NOT_FOUND")
        payload = {"observation_id": str(source.id), "quantity": source.quantity, "product_level": source.product_level, "product_group": source.product_group, "product_class": source.product_class}
        semantic = {"event_type": event_type, "company_id": str(company_id), "source_entity_type": "actual_weekly_observation", "source_entity_id": str(source.id), "source_revision_identity": "accepted_observation:" + str(source.id), "material_code": source.material_code, "demand_type": source.demand_type, "affected_period": source.period, "payload": payload}
        return self._base({"material_code": source.material_code, "demand_type": source.demand_type, "source_entity_type": "actual_weekly_observation", "source_entity_id": source.id, "source_revision_identity": semantic["source_revision_identity"], "affected_start_period": source.period, "affected_end_period": source.period, "evidence_payload": payload, "occurred_at": source.accepted_at}, semantic)

    def _actual_corrected(self, session, company_id, source_id, event_type):
        revision = session.query(ActualWeeklyRevision).filter_by(id=source_id, company_id=company_id).one_or_none()
        if revision is None or revision.approval_status != "accepted" or revision.change_type != "correction" or revision.observation_id is None:
            raise ValueError("ACCEPTED_ACTUAL_CORRECTION_REQUIRED")
        observation = session.query(ActualWeeklyObservation).filter_by(id=revision.observation_id, company_id=company_id).one_or_none()
        if observation is None:
            raise ValueError("ACTUAL_CORRECTION_OBSERVATION_UNAVAILABLE")
        previous = session.query(LearningEvidence).filter(
            LearningEvidence.company_id == company_id,
            LearningEvidence.source_entity_type == "actual_weekly_observation",
            LearningEvidence.source_entity_id == observation.id,
            LearningEvidence.event_type.in_(("ACTUAL_ACCEPTED", "ACTUAL_CORRECTED")),
        ).order_by(LearningEvidence.recorded_at.desc(), LearningEvidence.id.desc()).first()
        payload = {"observation_id": str(observation.id), "revision_id": str(revision.id), "previous_quantity": revision.previous_quantity, "accepted_quantity": observation.quantity, "product_level": observation.product_level, "product_group": observation.product_group, "product_class": observation.product_class}
        revision_identity = "accepted_revision:" + str(revision.id)
        semantic = {"event_type": event_type, "company_id": str(company_id), "source_entity_type": "actual_weekly_observation", "source_entity_id": str(observation.id), "source_revision_identity": revision_identity, "material_code": observation.material_code, "demand_type": observation.demand_type, "affected_period": observation.period, "payload": payload}
        return self._base({"material_code": observation.material_code, "demand_type": observation.demand_type, "source_entity_type": "actual_weekly_observation", "source_entity_id": observation.id, "source_revision_identity": revision_identity, "affected_start_period": observation.period, "affected_end_period": observation.period, "evidence_payload": payload, "occurred_at": revision.approved_at or revision.created_at or datetime.now(timezone.utc), "supersedes_evidence_id": previous.id if previous else None}, semantic)

    def _forecast_evaluated(self, session, company_id, source_id, event_type):
        evaluation = session.query(ForecastEvaluation).filter_by(id=source_id, company_id=company_id).one_or_none()
        if evaluation is None:
            raise LookupError("FORECAST_EVALUATION_NOT_FOUND")
        points = session.query(ForecastEvaluationPoint).filter_by(evaluation_id=evaluation.id).order_by(ForecastEvaluationPoint.material_code, ForecastEvaluationPoint.target_period, ForecastEvaluationPoint.id).all()
        if not points:
            raise ValueError("FORECAST_EVALUATION_POINTS_REQUIRED")
        materials = sorted({point.material_code for point in points})
        material = materials[0] if len(materials) == 1 else None
        payload = {"evaluation_id": str(evaluation.id), "point_ids": [str(point.id) for point in points], "material_codes": materials, "metrics": {"wape": evaluation.wape, "mean_signed_error": evaluation.mean_signed_error, "mae": evaluation.mae, "rmse": evaluation.rmse, "smape": evaluation.smape, "point_count": evaluation.evaluated_point_count, "metric_contract_version": evaluation.metric_contract_version}}
        revision_identity = "forecast_evaluation:" + str(evaluation.id) + ":" + evaluation.metric_contract_version
        semantic = {"event_type": event_type, "company_id": str(company_id), "source_entity_type": "forecast_evaluation", "source_entity_id": str(evaluation.id), "source_revision_identity": revision_identity, "material_code": material, "demand_type": evaluation.demand_type, "affected_periods": [evaluation.start_period, evaluation.end_period], "payload": payload}
        return self._base({"material_code": material, "demand_type": evaluation.demand_type, "source_entity_type": "forecast_evaluation", "source_entity_id": evaluation.id, "source_revision_identity": revision_identity, "affected_start_period": evaluation.start_period, "affected_end_period": evaluation.end_period, "evidence_payload": payload, "occurred_at": evaluation.recalculated_at}, semantic)

    def _champion_transition(self, session, company_id, source_id, event_type):
        transition = session.query(ChampionRegistryTransition).filter_by(id=source_id, company_id=company_id).one_or_none()
        expected = "PROMOTION" if event_type == "CHAMPION_PROMOTED" else "ROLLBACK"
        if transition is None or transition.transition_type != expected:
            raise ValueError("CHAMPION_TRANSITION_SOURCE_MISMATCH")
        payload = {"transition_id": str(transition.id), "transition_type": transition.transition_type, "source_entry_id": str(transition.source_entry_id) if transition.source_entry_id else None, "destination_entry_id": str(transition.destination_entry_id), "source_decision_id": str(transition.source_decision_id) if transition.source_decision_id else None, "reason": transition.reason, "expected_current_entry_id": str(transition.expected_current_entry_id) if transition.expected_current_entry_id else None}
        revision_identity = "champion_transition:" + str(transition.id)
        semantic = {"event_type": event_type, "company_id": str(company_id), "source_entity_type": "champion_registry_transition", "source_entity_id": str(transition.id), "source_revision_identity": revision_identity, "material_code": transition.material_code, "demand_type": transition.demand_type, "payload": payload}
        return self._base({"material_code": transition.material_code, "demand_type": transition.demand_type, "source_entity_type": "champion_registry_transition", "source_entity_id": transition.id, "source_revision_identity": revision_identity, "evidence_payload": payload, "occurred_at": transition.created_at or datetime.now(timezone.utc)}, semantic)

    def _retraining_completed(self, session, company_id, source_id, event_type):
        job = session.query(RetrainingJob).filter_by(id=source_id, company_id=company_id).one_or_none()
        if job is None or job.state not in TERMINAL_RETRAINING_STATES:
            raise ValueError("TERMINAL_RETRAINING_JOB_REQUIRED")
        payload = {"job_id": str(job.id), "state": job.state, "model_artifact_id": str(job.model_artifact_id) if job.model_artifact_id else None, "eligibility_tier": job.eligibility_tier, "reason_codes": job.eligibility_reason_codes, "evaluation_evidence_fingerprint": job.evaluation_evidence_fingerprint, "candidate_fingerprint": job.candidate_fingerprint}
        revision_identity = "retraining_terminal:" + str(job.id) + ":" + job.state + ":" + (str(job.model_artifact_id) if job.model_artifact_id else "none")
        semantic = {"event_type": event_type, "company_id": str(company_id), "source_entity_type": "retraining_job", "source_entity_id": str(job.id), "source_revision_identity": revision_identity, "material_code": job.material_code, "demand_type": job.demand_type, "affected_periods": [job.evaluation_start_period, job.evaluation_end_period], "payload": payload}
        return self._base({"material_code": job.material_code, "demand_type": job.demand_type, "source_entity_type": "retraining_job", "source_entity_id": job.id, "source_revision_identity": revision_identity, "affected_start_period": job.evaluation_start_period, "affected_end_period": job.evaluation_end_period, "evidence_payload": payload, "occurred_at": job.completed_at or job.created_at or datetime.now(timezone.utc)}, semantic)

    def _supplier_delivery_observed(self, session, company_id, source_id, event_type):
        observation = session.query(SupplierDeliveryObservation).filter_by(id=source_id, company_id=company_id).one_or_none()
        if observation is None:
            raise LookupError("SUPPLIER_DELIVERY_OBSERVATION_NOT_FOUND")
        payload = {"observation_id": str(observation.id), "supplier_id": str(observation.supplier_id),
                   "material_code": observation.material_code, "receipt_date": observation.actual_receipt_date,
                   "evidence_fingerprint": observation.current_evidence_fingerprint}
        revision_identity = "supplier_delivery_observation:" + str(observation.id) + ":" + observation.current_evidence_fingerprint
        semantic = {"event_type": event_type, "company_id": str(company_id), "source_entity_type": "supplier_delivery_observation",
                    "source_entity_id": str(observation.id), "source_revision_identity": revision_identity,
                    "material_code": observation.material_code, "supplier_id": str(observation.supplier_id), "payload": payload}
        return self._base({"material_code": observation.material_code, "demand_type": None,
                           "source_entity_type": "supplier_delivery_observation", "source_entity_id": observation.id,
                           "source_revision_identity": revision_identity, "evidence_payload": payload,
                           "occurred_at": observation.occurred_at}, semantic)

    def _supplier_delivery_corrected(self, session, company_id, source_id, event_type):
        revision = session.query(SupplierDeliveryObservationRevision).filter_by(id=source_id, company_id=company_id).one_or_none()
        if revision is None or revision.approval_status != "accepted":
            raise ValueError("ACCEPTED_SUPPLIER_DELIVERY_CORRECTION_REQUIRED")
        observation = session.query(SupplierDeliveryObservation).filter_by(id=revision.observation_id, company_id=company_id).one_or_none()
        if observation is None:
            raise ValueError("SUPPLIER_DELIVERY_CORRECTION_OBSERVATION_UNAVAILABLE")
        previous = session.query(LearningEvidence).filter(
            LearningEvidence.company_id == company_id, LearningEvidence.source_entity_type == "supplier_delivery_observation",
            LearningEvidence.source_entity_id == observation.id,
            LearningEvidence.event_type.in_(("SUPPLIER_DELIVERY_OBSERVED", "SUPPLIER_DELIVERY_CORRECTED")),
        ).order_by(LearningEvidence.recorded_at.desc(), LearningEvidence.id.desc()).first()
        payload = {"observation_id": str(observation.id), "revision_id": str(revision.id), "supplier_id": str(observation.supplier_id),
                   "material_code": observation.material_code, "accepted_evidence_fingerprint": observation.current_evidence_fingerprint}
        revision_identity = "accepted_supplier_delivery_revision:" + str(revision.id)
        semantic = {"event_type": event_type, "company_id": str(company_id), "source_entity_type": "supplier_delivery_observation",
                    "source_entity_id": str(observation.id), "source_revision_identity": revision_identity,
                    "material_code": observation.material_code, "supplier_id": str(observation.supplier_id), "payload": payload}
        return self._base({"material_code": observation.material_code, "demand_type": None,
                           "source_entity_type": "supplier_delivery_observation", "source_entity_id": observation.id,
                           "source_revision_identity": revision_identity, "evidence_payload": payload,
                           "occurred_at": revision.approved_at or revision.created_at or datetime.now(timezone.utc),
                           "supersedes_evidence_id": previous.id if previous else None}, semantic)

    @staticmethod
    def _event_snapshot(revision):
        snapshot = dict(revision.proposed_snapshot)
        return snapshot

    def _event_observed(self, session, company_id, source_id, event_type):
        event = session.query(EventObservation).filter_by(id=source_id, company_id=company_id).one_or_none()
        if event is None or event.current_revision_id is None:
            raise LookupError("EVENT_OBSERVATION_NOT_FOUND")
        revision = session.query(EventRevision).filter_by(id=event.current_revision_id, company_id=company_id, event_observation_id=event.id, approval_status="accepted").one_or_none()
        if revision is None:
            raise ValueError("ACCEPTED_EVENT_OBSERVATION_REQUIRED")
        return self._event_evidence(session, company_id, event, revision, event_type, supersedes=False)

    def _event_revision(self, session, company_id, source_id, event_type):
        revision = session.query(EventRevision).filter_by(id=source_id, company_id=company_id, approval_status="accepted").one_or_none()
        if revision is None:
            raise ValueError("ACCEPTED_EVENT_REVISION_REQUIRED")
        event = session.query(EventObservation).filter_by(id=revision.event_observation_id, company_id=company_id).one_or_none()
        if event is None:
            raise ValueError("EVENT_REVISION_OBSERVATION_UNAVAILABLE")
        snapshot = self._event_snapshot(revision)
        is_cancelled = snapshot.get("status") == "CANCELLED"
        if (event_type == "EVENT_CANCELLED") != is_cancelled:
            raise ValueError("EVENT_CANCELLATION_SOURCE_MISMATCH")
        return self._event_evidence(session, company_id, event, revision, event_type, supersedes=True)

    def _event_evidence(self, session, company_id, event, revision, event_type, *, supersedes):
        snapshot=self._event_snapshot(revision)
        demand=snapshot["demand_type"]; start=snapshot["start_date"]; end=snapshot["end_date"]
        payload={"event_id":str(event.id),"revision_id":str(revision.id),"event_identity":snapshot["event_identity"],"event_type":snapshot["event_type"],"scope_type":snapshot["scope_type"],"scope_value":snapshot.get("scope_value"),"demand_type":demand,"start_date":start,"end_date":end,"status":snapshot["status"],"event_evidence_fingerprint":revision.proposed_evidence_fingerprint}
        if supersedes:
            payload["previous_snapshot"] = revision.previous_snapshot
        identity=("event_observation:"+str(event.id)+":"+str(revision.id))
        previous=None
        if supersedes:
            previous=session.query(LearningEvidence).filter(LearningEvidence.company_id==company_id,LearningEvidence.source_entity_type=="event_observation",LearningEvidence.source_entity_id==event.id,LearningEvidence.event_type.in_(("EVENT_OBSERVED","EVENT_CORRECTED","EVENT_CANCELLED"))).order_by(LearningEvidence.recorded_at.desc(),LearningEvidence.id.desc()).first()
        semantic={"event_type":event_type,"company_id":str(company_id),"source_entity_type":"event_observation","source_entity_id":str(event.id),"source_revision_identity":identity,"event_identity":snapshot["event_identity"],"demand_type":demand,"scope":[snapshot["scope_type"],snapshot.get("scope_value")],"periods":[event.start_period,event.end_period],"payload":payload}
        return self._base({"material_code":snapshot.get("scope_value") if snapshot["scope_type"]=="MATERIAL" else None,"demand_type":demand,"source_entity_type":"event_observation","source_entity_id":event.id,"source_revision_identity":identity,"affected_start_period":event.start_period,"affected_end_period":event.end_period,"evidence_payload":payload,"occurred_at":revision.approved_at or revision.created_at or datetime.now(timezone.utc),"supersedes_evidence_id":previous.id if previous else None},semantic)
