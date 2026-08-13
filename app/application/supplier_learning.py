"""Deterministic, read-only supplier learning over canonical delivery observations."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
import math

from app.models.company import MaterialSupplier, Supplier, UserMaterial
from app.models.supplier_delivery_observation import (
    SupplierDeliveryObservation,
    SupplierDeliveryObservationRevision,
)


FEATURE_VERSION = "supplier_delivery_features_v1"
POLICY_VERSION = "supplier_learning_policy_v1"
CONFIDENCE_POLICY_VERSION = "supplier_learning_confidence_v1"
MIN_OBSERVED_LEAD_TIME_HISTORY = 8
RECENT_WINDOW = 4
MIN_RECENT_HISTORY = 12


class SupplierLearningError(ValueError):
    pass


@dataclass(frozen=True)
class SupplierLearningResult:
    company_id: object; supplier_id: object; supplier_code: str; supplier_name: str
    material_code: str; cutoff_date: date
    feature_version: str; policy_version: str; confidence_policy_version: str
    source_fingerprint: str; status: str; classification: str; confidence: float
    sample_count: int; lead_time_sample_count: int; first_receipt_date: date | None; last_receipt_date: date | None
    mean_observed_lead_time_days: float | None; median_observed_lead_time_days: float | None
    std_observed_lead_time_days: float | None; min_observed_lead_time_days: int | None; max_observed_lead_time_days: int | None
    p50_observed_lead_time_days: float | None; p90_observed_lead_time_days: float | None
    lead_time_coefficient_of_variation: float | None; lead_time_percentile_spread_days: float | None
    promised_delivery_sample_count: int; on_time_count: int; late_count: int
    on_time_ratio: float | None; late_ratio: float | None; mean_lateness_days: float | None
    fulfillment_sample_count: int; mean_fulfillment_ratio: float | None; underfulfillment_count: int; underfulfillment_ratio: float | None
    recent_window_size: int; recent_deterioration_evaluated: bool
    recent_lead_time_change_ratio: float | None; recent_late_ratio_change: float | None; recent_fulfillment_change_ratio: float | None
    recent_deterioration_dimensions: tuple[str, ...]
    product_level: str | None; product_group: str | None; product_class: str | None
    source_observation_ids: tuple[str, ...]; accepted_revision_ids: tuple[str, ...]


def _json_value(value):
    if isinstance(value, (date, Decimal)):
        return value.isoformat() if isinstance(value, date) else format(value, "f")
    return str(value) if value is not None and not isinstance(value, (str, int, float, bool, list, dict, tuple)) else value


def _fingerprint(payload):
    return sha256(json.dumps(payload, default=_json_value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _mean(values):
    return sum(values) / len(values) if values else None


def _std(values):
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) if mean is not None else None


def _percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return float(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower))


class SupplierLearningService:
    """Calculation-only boundary; no supplier mutation, memory, evidence, or runtime effects."""

    def __init__(self, session):
        self.session = session

    def calculate(self, company_id, supplier_id, material_code, cutoff_date):
        if not isinstance(cutoff_date, date):
            raise SupplierLearningError("SUPPLIER_LEARNING_CUTOFF_DATE_REQUIRED")
        supplier, material = self._scope(company_id, supplier_id, material_code)
        rows = self.session.query(SupplierDeliveryObservation).filter(
            SupplierDeliveryObservation.company_id == company_id,
            SupplierDeliveryObservation.supplier_id == supplier_id,
            SupplierDeliveryObservation.material_code == material_code,
            SupplierDeliveryObservation.actual_receipt_date <= cutoff_date,
        ).order_by(SupplierDeliveryObservation.actual_receipt_date, SupplierDeliveryObservation.id).all()
        source_ids = tuple(str(row.id) for row in rows)
        revisions = self.session.query(SupplierDeliveryObservationRevision).filter(
            SupplierDeliveryObservationRevision.company_id == company_id,
            SupplierDeliveryObservationRevision.observation_id.in_([row.id for row in rows]),
            SupplierDeliveryObservationRevision.approval_status == "accepted",
        ).order_by(SupplierDeliveryObservationRevision.id).all() if rows else []
        revision_ids = tuple(str(row.id) for row in revisions)
        fp = _fingerprint({
            "company_id": company_id, "supplier_id": supplier_id, "material_code": material_code,
            "cutoff_date": cutoff_date, "feature_version": FEATURE_VERSION, "policy_version": POLICY_VERSION,
            "observations": [(row.id, row.current_evidence_fingerprint, row.actual_receipt_date) for row in rows],
            "accepted_revisions": [(row.id, row.proposed_evidence_fingerprint) for row in revisions],
        })
        lead_rows = [row for row in rows if row.observed_lead_time_days is not None]
        lead_values = [float(row.observed_lead_time_days) for row in lead_rows]
        promise_rows = [row for row in rows if row.promised_delivery_date is not None]
        quantity_rows = [row for row in rows if row.ordered_quantity is not None and row.received_quantity is not None and row.ordered_quantity > 0]
        common = dict(
            company_id=company_id, supplier_id=supplier_id, supplier_code=supplier.code, supplier_name=supplier.name,
            material_code=material_code, cutoff_date=cutoff_date, feature_version=FEATURE_VERSION,
            policy_version=POLICY_VERSION, confidence_policy_version=CONFIDENCE_POLICY_VERSION,
            source_fingerprint=fp, sample_count=len(rows), lead_time_sample_count=len(lead_rows),
            first_receipt_date=rows[0].actual_receipt_date if rows else None,
            last_receipt_date=rows[-1].actual_receipt_date if rows else None,
            product_level=material.product_level, product_group=material.group, product_class=material.product_class,
            source_observation_ids=source_ids, accepted_revision_ids=revision_ids,
        )
        metrics = self._metrics(lead_values, promise_rows, quantity_rows)
        if not rows:
            return SupplierLearningResult(**common, status="ABSENT", classification="INSUFFICIENT_HISTORY", confidence=0.0,
                recent_window_size=0, recent_deterioration_evaluated=False, recent_lead_time_change_ratio=None,
                recent_late_ratio_change=None, recent_fulfillment_change_ratio=None, recent_deterioration_dimensions=(), **metrics)
        if len(lead_rows) < MIN_OBSERVED_LEAD_TIME_HISTORY:
            return SupplierLearningResult(**common, status="INSUFFICIENT_HISTORY", classification="INSUFFICIENT_HISTORY", confidence=0.0,
                recent_window_size=0, recent_deterioration_evaluated=False, recent_lead_time_change_ratio=None,
                recent_late_ratio_change=None, recent_fulfillment_change_ratio=None, recent_deterioration_dimensions=(), **metrics)
        recent = self._recent(lead_rows, promise_rows, quantity_rows)
        classification = self._classification(metrics, recent)
        confidence = self._confidence(len(lead_rows), len(rows), len(promise_rows), len(quantity_rows), cutoff_date, rows[-1].actual_receipt_date)
        return SupplierLearningResult(**common, status="OK", classification=classification, confidence=confidence, **recent, **metrics)

    def _scope(self, company_id, supplier_id, material_code):
        supplier = self.session.query(Supplier).filter_by(id=supplier_id, company_id=company_id).one_or_none()
        material = self.session.query(UserMaterial).filter_by(company_id=company_id, material_code=material_code).one_or_none()
        if supplier is None or material is None or self.session.query(MaterialSupplier).filter_by(material_id=material.id, supplier_id=supplier_id).one_or_none() is None:
            raise SupplierLearningError("SUPPLIER_LEARNING_SCOPE_UNAVAILABLE")
        return supplier, material

    @staticmethod
    def _metrics(leads, promise_rows, quantity_rows):
        mean = _mean(leads); std = _std(leads); p50 = _percentile(leads, .50); p90 = _percentile(leads, .90)
        late_count = sum(row.delivery_lateness_days > 0 for row in promise_rows)
        lateness = [float(row.delivery_lateness_days) for row in promise_rows]
        fulfillment = [float(row.received_quantity / row.ordered_quantity) for row in quantity_rows]
        under_count = sum(value < 1.0 for value in fulfillment)
        return dict(
            mean_observed_lead_time_days=mean, median_observed_lead_time_days=p50, std_observed_lead_time_days=std,
            min_observed_lead_time_days=int(min(leads)) if leads else None, max_observed_lead_time_days=int(max(leads)) if leads else None,
            p50_observed_lead_time_days=p50, p90_observed_lead_time_days=p90,
            lead_time_coefficient_of_variation=(std / mean if std is not None and mean else None),
            lead_time_percentile_spread_days=(p90 - p50 if p90 is not None and p50 is not None else None),
            promised_delivery_sample_count=len(promise_rows), on_time_count=len(promise_rows) - late_count, late_count=late_count,
            on_time_ratio=((len(promise_rows) - late_count) / len(promise_rows) if promise_rows else None),
            late_ratio=(late_count / len(promise_rows) if promise_rows else None),
            mean_lateness_days=_mean(lateness), fulfillment_sample_count=len(quantity_rows),
            mean_fulfillment_ratio=_mean(fulfillment), underfulfillment_count=under_count,
            underfulfillment_ratio=(under_count / len(fulfillment) if fulfillment else None),
        )

    def _recent(self, lead_rows, promise_rows, quantity_rows):
        if len(lead_rows) < MIN_RECENT_HISTORY:
            return dict(recent_window_size=0, recent_deterioration_evaluated=False, recent_lead_time_change_ratio=None,
                recent_late_ratio_change=None, recent_fulfillment_change_ratio=None, recent_deterioration_dimensions=())
        boundary = lead_rows[-RECENT_WINDOW].actual_receipt_date
        base_leads = [float(row.observed_lead_time_days) for row in lead_rows if row.actual_receipt_date < boundary]
        recent_leads = [float(row.observed_lead_time_days) for row in lead_rows if row.actual_receipt_date >= boundary]
        lead_change = (_mean(recent_leads) - _mean(base_leads)) / max(abs(_mean(base_leads)), 1.0)
        def ratio(rows, predicate): return sum(predicate(row) for row in rows) / len(rows) if rows else None
        base_promises = [row for row in promise_rows if row.actual_receipt_date < boundary]
        recent_promises = [row for row in promise_rows if row.actual_receipt_date >= boundary]
        base_late, recent_late = ratio(base_promises, lambda row: row.delivery_lateness_days > 0), ratio(recent_promises, lambda row: row.delivery_lateness_days > 0)
        late_change = recent_late - base_late if base_late is not None and recent_late is not None and len(base_promises) >= RECENT_WINDOW and len(recent_promises) >= RECENT_WINDOW else None
        base_quantity = [float(row.received_quantity / row.ordered_quantity) for row in quantity_rows if row.actual_receipt_date < boundary]
        recent_quantity = [float(row.received_quantity / row.ordered_quantity) for row in quantity_rows if row.actual_receipt_date >= boundary]
        fulfillment_change = ((_mean(recent_quantity) - _mean(base_quantity)) / max(abs(_mean(base_quantity)), 1.0)
            if len(base_quantity) >= RECENT_WINDOW and len(recent_quantity) >= RECENT_WINDOW else None)
        dimensions = tuple(name for name, enabled in (
            ("LEAD_TIME_INCREASE", lead_change >= .25 and (_mean(recent_leads) - _mean(base_leads)) >= 2.0),
            ("LATE_RATIO_INCREASE", late_change is not None and late_change >= .25),
            ("FULFILLMENT_DETERIORATION", fulfillment_change is not None and fulfillment_change <= -.10),
        ) if enabled)
        return dict(recent_window_size=RECENT_WINDOW, recent_deterioration_evaluated=True, recent_lead_time_change_ratio=lead_change,
            recent_late_ratio_change=late_change, recent_fulfillment_change_ratio=fulfillment_change,
            recent_deterioration_dimensions=dimensions)

    @staticmethod
    def _classification(metrics, recent):
        risks = []
        # 0.40 keeps a sustained lead-time shift distinct from genuinely broad
        # lead-time dispersion under the conservative v1 policy.
        if metrics["lead_time_coefficient_of_variation"] is not None and metrics["lead_time_coefficient_of_variation"] >= .40:
            risks.append("VARIABLE")
        if metrics["late_ratio"] is not None and metrics["late_ratio"] >= .25:
            risks.append("LATE_PRONE")
        if ((metrics["mean_fulfillment_ratio"] is not None and metrics["mean_fulfillment_ratio"] < .95) or
                (metrics["underfulfillment_ratio"] is not None and metrics["underfulfillment_ratio"] >= .20)):
            risks.append("FULFILLMENT_RISK")
        if recent["recent_deterioration_dimensions"]:
            risks.append("DETERIORATING")
        if not risks:
            return "RELIABLE"
        return risks[0] if len(risks) == 1 else "MIXED_RISK"

    @staticmethod
    def _confidence(lead_count, sample_count, promise_count, quantity_count, cutoff, latest):
        recency = max(0.0, 1.0 - max((cutoff - latest).days, 0) / 180.0)
        return round(min(.95, min(lead_count / 16.0, 1.0) * .50 + (promise_count / sample_count) * .20 +
                         (quantity_count / sample_count) * .20 + recency * .10), 3)
