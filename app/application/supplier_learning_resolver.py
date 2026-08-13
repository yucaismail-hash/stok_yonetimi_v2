"""Read-only, cutoff-safe resolver for durable Supplier Learning context."""
from dataclasses import dataclass
from datetime import date

from app.database import SessionLocal
from app.models.supplier_learning_memory import SupplierLearningMemory


@dataclass(frozen=True)
class SupplierLearningResolution:
    status: str; company_id: object; supplier_id: object; material_code: str
    memory_id: object | None = None; evidence: dict | None = None


class SupplierLearningResolver:
    """Never refreshes or writes; it only exposes compatible current provenance."""
    def __init__(self, session_factory=SessionLocal): self._sf = session_factory

    def resolve(self, company_id, supplier_id, material_code, *, cutoff_date: date | None = None):
        session = self._sf()
        try:
            memory = session.query(SupplierLearningMemory).filter_by(
                company_id=company_id, supplier_id=supplier_id, material_code=material_code).one_or_none()
            if memory is None:
                return SupplierLearningResolution("NO_LEARNED_SUPPLIER_EVIDENCE", company_id, supplier_id, material_code)
            if cutoff_date is not None and memory.cutoff_date > cutoff_date:
                return SupplierLearningResolution("LEARNING_CUTOFF_INCOMPATIBLE", company_id, supplier_id, material_code, memory.id)
            evidence = {"supplier_learning_available": True, "supplier_learning_memory_id": str(memory.id),
                "supplier_learning_classification": memory.classification, "supplier_learning_confidence": float(memory.confidence),
                "supplier_learning_cutoff": memory.cutoff_date.isoformat(), "supplier_learning_source_fingerprint": memory.source_fingerprint,
                "observed_lead_time_mean_days": float(memory.mean_observed_lead_time_days) if memory.mean_observed_lead_time_days is not None else None,
                "observed_lead_time_std_days": float(memory.std_observed_lead_time_days) if memory.std_observed_lead_time_days is not None else None,
                "on_time_ratio": float(memory.on_time_ratio) if memory.on_time_ratio is not None else None,
                "late_ratio": float(memory.late_ratio) if memory.late_ratio is not None else None,
                "mean_fulfillment_ratio": float(memory.mean_fulfillment_ratio) if memory.mean_fulfillment_ratio is not None else None,
                "recent_deterioration_dimensions": list(memory.recent_deterioration_dimensions or [])}
            return SupplierLearningResolution("AVAILABLE", company_id, supplier_id, material_code, memory.id, evidence)
        finally: session.close()
