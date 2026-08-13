"""Company-scoped canonical Supplier Delivery Observation write boundary."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.company import MaterialSupplier, Supplier, User, UserMaterial
from app.models.supplier_delivery_observation import SupplierDeliveryObservation, SupplierDeliveryObservationRevision


SOURCE_SYSTEMS = {"erp", "wms", "manual_verified"}


class SupplierDeliveryObservationError(ValueError):
    pass


@dataclass(frozen=True)
class SupplierDeliveryObservationWriteResult:
    status: str
    observation_id: object
    source_identity_fingerprint: str
    current_evidence_fingerprint: str


@dataclass(frozen=True)
class SupplierDeliveryCorrectionResult:
    status: str
    revision_id: object
    observation_id: object
    current_evidence_fingerprint: str


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value) if value is not None and not isinstance(value, (str, int, float, bool, list, dict, tuple)) else value


def _digest(payload):
    return sha256(json.dumps(payload, default=_json_value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _evidence_fingerprint(payload):
    """Operational truth only; observation write time is never delivery identity."""
    return _digest({key: value for key, value in payload.items() if key != "occurred_at"})


class SupplierDeliveryObservationService:
    """Writes observed delivery facts only; it never invokes Supplier or Learning analysis."""

    def __init__(self, session_factory=SessionLocal):
        self._sf = session_factory

    def create(self, company_id, supplier_id, material_code, *, source_system, actual_receipt_date,
               purchase_order_reference=None, order_line_reference=None, receipt_reference=None,
               dispatch_date=None, promised_delivery_date=None, ordered_quantity=None,
               received_quantity=None, occurred_at=None, provenance=None):
        payload = self._normalize(company_id, supplier_id, material_code, source_system, actual_receipt_date,
            purchase_order_reference, order_line_reference, receipt_reference, dispatch_date, promised_delivery_date,
            ordered_quantity, received_quantity, occurred_at, provenance)
        session = self._sf()
        try:
            material = self._authorized_scope(session, company_id, supplier_id, material_code)
            identity = _digest({"company_id": company_id, "supplier_id": supplier_id, "material_code": material_code,
                "source_system": payload["source_system"], "purchase_order_reference": payload["purchase_order_reference"],
                "order_line_reference": payload["order_line_reference"], "receipt_reference": payload["receipt_reference"]})
            existing = session.query(SupplierDeliveryObservation).filter_by(company_id=company_id, source_identity_fingerprint=identity).one_or_none()
            if existing:
                if existing.current_evidence_fingerprint != _evidence_fingerprint(payload):
                    raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_CORRECTION_REQUIRED")
                return SupplierDeliveryObservationWriteResult("ALREADY_EXISTS", existing.id, identity, existing.current_evidence_fingerprint)
            row = SupplierDeliveryObservation(company_id=company_id, supplier_id=supplier_id, material_id=material.id,
                material_code=material_code, source_identity_fingerprint=identity, current_evidence_fingerprint=_evidence_fingerprint(payload), **payload)
            session.add(row)
            try:
                session.commit()
                return SupplierDeliveryObservationWriteResult("CREATED", row.id, identity, row.current_evidence_fingerprint)
            except IntegrityError:
                session.rollback()
                existing = session.query(SupplierDeliveryObservation).filter_by(company_id=company_id, source_identity_fingerprint=identity).one_or_none()
                if existing is None:
                    raise
                if existing.current_evidence_fingerprint != _evidence_fingerprint(payload):
                    raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_CORRECTION_REQUIRED")
                return SupplierDeliveryObservationWriteResult("ALREADY_EXISTS", existing.id, identity, existing.current_evidence_fingerprint)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def propose_correction(self, company_id, observation_id, actor_user_id, **changes):
        session = self._sf()
        try:
            observation = self._observation(session, company_id, observation_id)
            self._actor(session, company_id, actor_user_id)
            unknown = set(changes) - {"dispatch_date", "promised_delivery_date", "actual_receipt_date", "ordered_quantity", "received_quantity", "provenance"}
            if unknown:
                raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_CORRECTION_FIELD_UNSUPPORTED")
            previous = self._snapshot(observation)
            candidate = {**self._current_changeable(observation), **changes}
            payload = self._normalize(company_id, observation.supplier_id, observation.material_code, observation.source_system,
                candidate["actual_receipt_date"], observation.purchase_order_reference, observation.order_line_reference,
                observation.receipt_reference, candidate.get("dispatch_date"), candidate.get("promised_delivery_date"),
                candidate.get("ordered_quantity"), candidate.get("received_quantity"), observation.occurred_at,
                candidate.get("provenance"))
            proposed = self._snapshot_payload(payload)
            proposed_fingerprint = _evidence_fingerprint(payload)
            correction_fingerprint = _digest({"observation_id": observation.id, "previous": observation.current_evidence_fingerprint,
                                               "proposed": proposed_fingerprint})
            existing = session.query(SupplierDeliveryObservationRevision).filter_by(company_id=company_id, correction_fingerprint=correction_fingerprint).one_or_none()
            if existing:
                return SupplierDeliveryCorrectionResult("ALREADY_EXISTS", existing.id, observation.id, existing.proposed_evidence_fingerprint)
            revision = SupplierDeliveryObservationRevision(company_id=company_id, observation_id=observation.id, actor_user_id=actor_user_id,
                previous_snapshot=previous, proposed_snapshot=proposed, previous_evidence_fingerprint=observation.current_evidence_fingerprint,
                proposed_evidence_fingerprint=proposed_fingerprint, correction_fingerprint=correction_fingerprint)
            session.add(revision)
            try:
                session.commit()
                return SupplierDeliveryCorrectionResult("PROPOSED", revision.id, observation.id, proposed_fingerprint)
            except IntegrityError:
                session.rollback()
                existing = session.query(SupplierDeliveryObservationRevision).filter_by(company_id=company_id, correction_fingerprint=correction_fingerprint).one_or_none()
                if existing is None:
                    raise
                return SupplierDeliveryCorrectionResult("ALREADY_EXISTS", existing.id, observation.id, existing.proposed_evidence_fingerprint)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def accept_correction(self, company_id, revision_id, actor_user_id):
        return self._decide(company_id, revision_id, actor_user_id, accepted=True)

    def reject_correction(self, company_id, revision_id, actor_user_id):
        return self._decide(company_id, revision_id, actor_user_id, accepted=False)

    def get(self, company_id, observation_id):
        session = self._sf()
        try:
            return session.query(SupplierDeliveryObservation).filter_by(id=observation_id, company_id=company_id).one_or_none()
        finally:
            session.close()

    def lineage(self, company_id, observation_id):
        session = self._sf()
        try:
            return tuple(session.query(SupplierDeliveryObservationRevision).filter_by(company_id=company_id, observation_id=observation_id)
                         .order_by(SupplierDeliveryObservationRevision.created_at, SupplierDeliveryObservationRevision.id).all())
        finally:
            session.close()

    def _decide(self, company_id, revision_id, actor_user_id, *, accepted):
        session = self._sf()
        try:
            self._actor(session, company_id, actor_user_id)
            revision = session.query(SupplierDeliveryObservationRevision).filter_by(id=revision_id, company_id=company_id).with_for_update().one_or_none()
            if revision is None or revision.approval_status != "proposed":
                raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_PENDING_CORRECTION_UNAVAILABLE")
            observation = self._observation(session, company_id, revision.observation_id)
            if accepted:
                if observation.current_evidence_fingerprint != revision.previous_evidence_fingerprint:
                    raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_CORRECTION_STALE")
                self._apply_snapshot(observation, revision.proposed_snapshot, revision.proposed_evidence_fingerprint)
                revision.approval_status = "accepted"; revision.approved_at = datetime.now(timezone.utc)
                status = "ACCEPTED"
            else:
                revision.approval_status = "rejected"; revision.rejected_at = datetime.now(timezone.utc)
                status = "REJECTED"
            session.commit()
            return SupplierDeliveryCorrectionResult(status, revision.id, observation.id, observation.current_evidence_fingerprint)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _observation(session, company_id, observation_id):
        row = session.query(SupplierDeliveryObservation).filter_by(id=observation_id, company_id=company_id).one_or_none()
        if row is None:
            raise LookupError("SUPPLIER_DELIVERY_OBSERVATION_NOT_FOUND")
        return row

    @staticmethod
    def _actor(session, company_id, user_id):
        if session.query(User).filter_by(id=user_id, company_id=company_id).one_or_none() is None:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_ACTOR_UNAUTHORIZED")

    @staticmethod
    def _authorized_scope(session, company_id, supplier_id, material_code):
        supplier = session.query(Supplier).filter_by(id=supplier_id, company_id=company_id).one_or_none()
        material = session.query(UserMaterial).filter_by(company_id=company_id, material_code=material_code).one_or_none()
        if supplier is None or material is None:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_SCOPE_UNAVAILABLE")
        mapping = session.query(MaterialSupplier).filter_by(material_id=material.id, supplier_id=supplier.id).one_or_none()
        if mapping is None:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_SUPPLIER_MATERIAL_MISMATCH")
        return material

    @staticmethod
    def _date(value, name, *, required=False):
        if value is None and not required:
            return None
        if not isinstance(value, date) or isinstance(value, datetime):
            raise SupplierDeliveryObservationError(f"{name} must be a date")
        return value

    @staticmethod
    def _quantity(value, name, *, positive=False):
        if value is None:
            return None
        if isinstance(value, bool):
            raise SupplierDeliveryObservationError(f"{name} must be numeric")
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise SupplierDeliveryObservationError(f"{name} must be numeric") from exc
        if not number.is_finite() or (positive and number <= 0) or (not positive and number < 0):
            raise SupplierDeliveryObservationError(f"{name} is invalid")
        return number

    def _normalize(self, company_id, supplier_id, material_code, source_system, actual_receipt_date,
                   purchase_order_reference, order_line_reference, receipt_reference, dispatch_date,
                   promised_delivery_date, ordered_quantity, received_quantity, occurred_at, provenance):
        if source_system not in SOURCE_SYSTEMS:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_SOURCE_SYSTEM_UNSUPPORTED")
        if not isinstance(material_code, str) or not material_code:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_MATERIAL_REQUIRED")
        references = (purchase_order_reference, order_line_reference, receipt_reference)
        if not any(isinstance(value, str) and value for value in references):
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_SOURCE_REFERENCE_REQUIRED")
        if any(value is not None and (not isinstance(value, str) or not value) for value in references):
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_SOURCE_REFERENCE_INVALID")
        receipt = self._date(actual_receipt_date, "actual_receipt_date", required=True)
        dispatch = self._date(dispatch_date, "dispatch_date")
        promised = self._date(promised_delivery_date, "promised_delivery_date")
        if dispatch and dispatch > receipt:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_DISPATCH_AFTER_RECEIPT")
        ordered = self._quantity(ordered_quantity, "ordered_quantity", positive=True)
        received = self._quantity(received_quantity, "received_quantity")
        if received is not None and ordered is None:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_ORDERED_QUANTITY_REQUIRED")
        if occurred_at is None:
            occurred_at = datetime.now(timezone.utc)
        if not isinstance(occurred_at, datetime) or occurred_at.tzinfo is None:
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_OCCURRED_AT_REQUIRED")
        if provenance is None:
            provenance = {}
        if not isinstance(provenance, dict):
            raise SupplierDeliveryObservationError("SUPPLIER_DELIVERY_PROVENANCE_INVALID")
        return {"purchase_order_reference": purchase_order_reference, "order_line_reference": order_line_reference,
                "receipt_reference": receipt_reference, "dispatch_date": dispatch, "promised_delivery_date": promised,
                "actual_receipt_date": receipt, "ordered_quantity": ordered, "received_quantity": received,
                "observed_lead_time_days": (receipt - dispatch).days if dispatch else None,
                "delivery_lateness_days": (receipt - promised).days if promised else None,
                "on_time": ((receipt - promised).days <= 0) if promised else None,
                "occurred_at": occurred_at, "source_system": source_system, "provenance": provenance}

    @staticmethod
    def _snapshot_payload(payload):
        return {key: _json_value(value) for key, value in payload.items() if key != "occurred_at"}

    def _snapshot(self, observation):
        return self._snapshot_payload({"dispatch_date": observation.dispatch_date, "promised_delivery_date": observation.promised_delivery_date,
            "actual_receipt_date": observation.actual_receipt_date, "ordered_quantity": observation.ordered_quantity,
            "received_quantity": observation.received_quantity, "provenance": observation.provenance})

    @staticmethod
    def _current_changeable(observation):
        return {"dispatch_date": observation.dispatch_date, "promised_delivery_date": observation.promised_delivery_date,
                "actual_receipt_date": observation.actual_receipt_date, "ordered_quantity": observation.ordered_quantity,
                "received_quantity": observation.received_quantity, "provenance": observation.provenance}

    def _apply_snapshot(self, observation, snapshot, fingerprint):
        payload = self._normalize(observation.company_id, observation.supplier_id, observation.material_code, observation.source_system,
            date.fromisoformat(snapshot["actual_receipt_date"]), observation.purchase_order_reference, observation.order_line_reference,
            observation.receipt_reference, date.fromisoformat(snapshot["dispatch_date"]) if snapshot.get("dispatch_date") else None,
            date.fromisoformat(snapshot["promised_delivery_date"]) if snapshot.get("promised_delivery_date") else None,
            snapshot.get("ordered_quantity"), snapshot.get("received_quantity"), observation.occurred_at, snapshot.get("provenance"))
        for key, value in payload.items():
            if key != "occurred_at":
                setattr(observation, key, value)
        observation.current_evidence_fingerprint = fingerprint
