"""Durable current projection for the read-only Supplier Learning calculation."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.application.supplier_learning import SupplierLearningService
from app.database import SessionLocal
from app.models.supplier_learning_memory import SupplierLearningMemory


@dataclass(frozen=True)
class SupplierLearningMaterializationResult:
    status: str
    memory_id: object | None
    row_version: int | None
    source_fingerprint: str | None


class SupplierLearningMaterializationService:
    """Persists only trusted SupplierLearningService results; no downstream integration."""

    def __init__(self, session_factory=SessionLocal):
        self._sf = session_factory

    def materialize(self, company_id, supplier_id, material_code, cutoff_date):
        session = self._sf()
        try:
            result = SupplierLearningService(session).calculate(company_id, supplier_id, material_code, cutoff_date)
            if result.status != "OK":
                return SupplierLearningMaterializationResult("NOT_MATERIALIZED", None, None, result.source_fingerprint)
            return self._persist(session, result)
        except IntegrityError:
            session.rollback()
            return self._recover(company_id, supplier_id, material_code, cutoff_date)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_current(self, company_id, supplier_id, material_code):
        session = self._sf()
        try:
            return session.query(SupplierLearningMemory).filter_by(
                company_id=company_id, supplier_id=supplier_id, material_code=material_code
            ).one_or_none()
        finally:
            session.close()

    def persist_result(self, result):
        """Explicit worker bridge with stale cutoff/fingerprint protection."""
        if result.status != "OK":
            return SupplierLearningMaterializationResult("NOT_MATERIALIZED", None, None, result.source_fingerprint)
        session = self._sf()
        try:
            return self._persist(session, result)
        except IntegrityError:
            session.rollback()
            return self._recover(result.company_id, result.supplier_id, result.material_code, result.cutoff_date)
        finally:
            session.close()

    def _persist(self, session, result):
        current = session.query(SupplierLearningMemory).filter_by(
            company_id=result.company_id, supplier_id=result.supplier_id, material_code=result.material_code
        ).with_for_update().one_or_none()
        if current and result.cutoff_date < current.cutoff_date:
            return SupplierLearningMaterializationResult("STALE_RESULT", current.id, current.row_version, current.source_fingerprint)
        if current and result.cutoff_date == current.cutoff_date and current.source_fingerprint != result.source_fingerprint:
            # A same-cutoff correction is valid only when this supplied result
            # still exactly represents current canonical evidence.  An older
            # worker result must never overwrite newer projection evidence.
            canonical = SupplierLearningService(session).calculate(
                result.company_id, result.supplier_id, result.material_code, result.cutoff_date
            )
            if canonical.status != "OK" or canonical.source_fingerprint != result.source_fingerprint:
                return SupplierLearningMaterializationResult("STALE_RESULT", current.id, current.row_version, current.source_fingerprint)
        values = self._values(result)
        if current:
            if current.source_fingerprint == result.source_fingerprint:
                return SupplierLearningMaterializationResult("UNCHANGED", current.id, current.row_version, current.source_fingerprint)
            for key, value in values.items():
                setattr(current, key, value)
            current.row_version += 1
            session.commit()
            return SupplierLearningMaterializationResult("UPDATED", current.id, current.row_version, current.source_fingerprint)
        current = SupplierLearningMemory(company_id=result.company_id, supplier_id=result.supplier_id,
            material_code=result.material_code, row_version=1, **values)
        session.add(current)
        session.commit()
        return SupplierLearningMaterializationResult("CREATED", current.id, 1, current.source_fingerprint)

    @staticmethod
    def _values(result):
        names = (
            "supplier_code", "supplier_name", "product_level", "product_group", "product_class",
            "policy_version", "feature_version", "confidence_policy_version", "classification", "confidence",
            "sample_count", "lead_time_sample_count", "first_receipt_date", "last_receipt_date", "cutoff_date",
            "mean_observed_lead_time_days", "median_observed_lead_time_days", "std_observed_lead_time_days",
            "lead_time_coefficient_of_variation", "min_observed_lead_time_days", "max_observed_lead_time_days",
            "p50_observed_lead_time_days", "p90_observed_lead_time_days", "lead_time_percentile_spread_days",
            "promised_delivery_sample_count", "on_time_count", "late_count", "on_time_ratio", "late_ratio",
            "mean_lateness_days", "fulfillment_sample_count", "mean_fulfillment_ratio", "underfulfillment_count",
            "underfulfillment_ratio", "recent_window_size", "recent_deterioration_evaluated",
            "recent_lead_time_change_ratio", "recent_late_ratio_change", "recent_fulfillment_change_ratio",
            "recent_deterioration_dimensions", "source_fingerprint", "source_observation_ids", "accepted_revision_ids",
        )
        values = {name: getattr(result, name) for name in names}
        values.update({
            "supplier_learning_policy_version": values.pop("policy_version"),
            "window_start": values.pop("first_receipt_date"),
            "window_end": values.pop("last_receipt_date"),
            "recent_deterioration_evaluated": "true" if values["recent_deterioration_evaluated"] else "false",
            "recent_deterioration_dimensions": list(values["recent_deterioration_dimensions"]),
            "source_observation_ids": list(values["source_observation_ids"]),
            "accepted_revision_ids": list(values["accepted_revision_ids"]),
            "last_materialized_at": datetime.now(timezone.utc),
        })
        return values

    def _recover(self, company_id, supplier_id, material_code, cutoff_date):
        current = self.get_current(company_id, supplier_id, material_code)
        if current is None:
            raise RuntimeError("SUPPLIER_LEARNING_MEMORY_CONCURRENCY_RECOVERY_UNAVAILABLE")
        status = "UNCHANGED" if current.cutoff_date == cutoff_date else "STALE_RESULT"
        return SupplierLearningMaterializationResult(status, current.id, current.row_version, current.source_fingerprint)
