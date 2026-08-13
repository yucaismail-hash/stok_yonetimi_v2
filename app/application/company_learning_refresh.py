"""Explicit, company-scoped refresh facade for the Company Learning projection."""
from dataclasses import dataclass
from time import perf_counter

from app.application.company_learning_materialization import CompanyLearningMaterializationService


@dataclass(frozen=True)
class CompanyLearningRefreshResult:
    company_id: object
    source_change_type: str | None
    status: str
    memory_id: object | None
    previous_fingerprint: str | None
    source_summary_fingerprint: str | None
    previous_row_version: int | None
    row_version: int | None
    previous_score: object | None
    score: object | None
    duration_ms: float
    failure_code: str | None = None


class CompanyLearningRefreshService:
    """Refreshes only caller-supplied companies; it never discovers companies."""

    def __init__(self, materialization_service=None, *, before_materialize=None, after_materialize=None):
        self._materializer = materialization_service or CompanyLearningMaterializationService()
        self._before = before_materialize
        self._after = after_materialize

    def refresh(self, company_id, *, source_change_type=None):
        started = perf_counter()
        previous = self._materializer.get_current(company_id)
        if self._before:
            self._before(company_id, source_change_type)
        result = self._materializer.materialize(company_id)
        current = self._materializer.get_current(company_id)
        response = CompanyLearningRefreshResult(
            company_id, source_change_type, result.status, result.memory_id,
            previous.source_summary_fingerprint if previous else None,
            result.source_summary_fingerprint,
            previous.row_version if previous else None, result.row_version,
            previous.evidence_maturity_score if previous else None,
            current.evidence_maturity_score if current else None,
            (perf_counter() - started) * 1000,
        )
        if self._after:
            self._after(response)
        return response

    def refresh_batch(self, requests):
        """Execute only explicit caller-selected company IDs; no global rescan."""
        return tuple(self.refresh(**request) for request in requests)
