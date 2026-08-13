"""Bounded, explicit worker for durable Learning refresh deliveries.

Deployment scheduling is intentionally outside this module.  A host may call
``process_next`` or a bounded ``process_batch``; there is no daemon or timer.
"""
from dataclasses import dataclass
from time import perf_counter

from app.application.learning_refresh_delivery import LearningRefreshDeliveryService


@dataclass(frozen=True)
class LearningRefreshWorkerResult:
    status: str
    company_id: object
    worker_id: str
    delivery_id: object | None
    learning_evidence_id: object | None
    attempt_count: int | None
    processing_duration_ms: float
    failure_code: str | None = None


class LearningRefreshWorker:
    """Claims work exclusively through the PostgreSQL delivery ledger."""

    def __init__(self, worker_id, delivery_service=None):
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker_id is required")
        self._worker_id = worker_id
        self._delivery = delivery_service or LearningRefreshDeliveryService()

    def process_next(self, company_id, *, exclude_delivery_ids=()):
        started = perf_counter()
        claim = self._delivery.claim_next(company_id, self._worker_id, exclude_delivery_ids=exclude_delivery_ids)
        if claim.status != "CLAIMED":
            return LearningRefreshWorkerResult(claim.status, company_id, self._worker_id, claim.delivery_id,
                claim.learning_evidence_id, claim.attempt_count, (perf_counter() - started) * 1000, claim.failure_code)
        return self.process_claimed(company_id, claim.delivery_id, claim.claim_token, started=started)

    def process_claimed(self, company_id, delivery_id, claim_token, *, started=None):
        """Finish an already-leased item; useful to explicit hosts after a handoff."""
        started = perf_counter() if started is None else started
        result = self._delivery.process_claimed(company_id, delivery_id, claim_token)
        return LearningRefreshWorkerResult(result.status, company_id, self._worker_id, result.delivery_id,
            result.learning_evidence_id, result.attempt_count, (perf_counter() - started) * 1000, result.failure_code)

    def process_batch(self, company_id, *, limit):
        """Process at most ``limit`` ledger items; failed work is not re-claimed in this batch."""
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        results, seen = [], set()
        for _ in range(limit):
            result = self.process_next(company_id, exclude_delivery_ids=seen)
            if result.status == "NO_WORK":
                break
            results.append(result)
            if result.delivery_id is not None:
                seen.add(result.delivery_id)
        return tuple(results)
