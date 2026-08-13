"""Exact-scope refresh boundary for durable Supplier Learning delivery."""
from dataclasses import dataclass
from time import perf_counter

from app.application.supplier_learning_materialization import SupplierLearningMaterializationService


@dataclass(frozen=True)
class SupplierLearningRefreshResult:
    company_id: object; supplier_id: object; material_code: str; cutoff_date: object
    status: str; memory_id: object | None; row_version: int | None
    source_fingerprint: str | None; duration_ms: float


class SupplierLearningRefreshService:
    """One caller-supplied supplier/material scope; deliberately no discovery scan."""
    def __init__(self, materialization_service=None):
        self._materialization = materialization_service or SupplierLearningMaterializationService()

    def refresh(self, company_id, supplier_id, material_code, cutoff_date):
        started = perf_counter()
        result = self._materialization.materialize(company_id, supplier_id, material_code, cutoff_date)
        return SupplierLearningRefreshResult(company_id, supplier_id, material_code, cutoff_date, result.status,
            result.memory_id, result.row_version, result.source_fingerprint, (perf_counter() - started) * 1000)
