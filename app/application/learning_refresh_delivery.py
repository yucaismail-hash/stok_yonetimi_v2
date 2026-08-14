"""Durable claim/lease ownership for explicit Learning refresh delivery workers."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import perf_counter

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from uuid_extensions import uuid7

from app.application.learning_refresh_orchestrator import (
    LearningEvidenceNotFound, LearningEvidenceTenantViolation, LearningRefreshOrchestrator, LearningRefreshRoutingError,
)
from app.database import SessionLocal
from app.models.learning_refresh_delivery import LearningRefreshDelivery


DELIVERY_CONTRACT_VERSION = "learning_refresh_delivery_v1"


class LearningRefreshDeliveryLeaseError(ValueError):
    pass


@dataclass(frozen=True)
class LearningRefreshDeliveryResult:
    status: str
    delivery_id: object | None
    company_id: object
    learning_evidence_id: object | None
    claim_token: object | None = None
    attempt_count: int | None = None
    state: str | None = None
    failure_code: str | None = None


class LearningRefreshDeliveryService:
    """No timer or global scan: explicit company-scoped intent/claim lifecycle only."""

    def __init__(self, session_factory=SessionLocal, *, lease_seconds=60, max_attempts=3, now_factory=None,
                 orchestrator_factory=LearningRefreshOrchestrator):
        if lease_seconds < 1 or max_attempts < 1:
            raise ValueError("lease_seconds and max_attempts must be positive")
        self._sf = session_factory; self._lease_seconds = lease_seconds; self._max_attempts = max_attempts
        self._now = now_factory or (lambda: datetime.now(timezone.utc)); self._orchestrator_factory = orchestrator_factory

    def get(self, company_id, delivery_id):
        s = self._sf()
        try:
            return s.query(LearningRefreshDelivery).filter_by(id=delivery_id, company_id=company_id).one_or_none()
        finally:
            s.close()

    def get_by_evidence(self, company_id, learning_evidence_id):
        s = self._sf()
        try:
            return s.query(LearningRefreshDelivery).filter_by(company_id=company_id, learning_evidence_id=learning_evidence_id,
                delivery_contract_version=DELIVERY_CONTRACT_VERSION).one_or_none()
        finally:
            s.close()

    def claim(self, company_id, delivery_id, worker_id):
        return self._claim(company_id, worker_id, delivery_id=delivery_id)

    def claim_next(self, company_id, worker_id, *, exclude_delivery_ids=()):
        """Bounded to one supplied tenant; intentionally no all-company discovery."""
        return self._claim(company_id, worker_id, delivery_id=None, exclude_delivery_ids=exclude_delivery_ids)

    def _claim(self, company_id, worker_id, *, delivery_id, exclude_delivery_ids=()):
        s = self._sf(); now = self._now()
        try:
            q = s.query(LearningRefreshDelivery).filter_by(company_id=company_id)
            if delivery_id is not None:
                delivery = q.filter_by(id=delivery_id).with_for_update().one_or_none()
            else:
                candidates = q.filter(or_(LearningRefreshDelivery.state == "pending",
                    (LearningRefreshDelivery.state == "processing") & (LearningRefreshDelivery.lease_expires_at <= now))) \
                    .order_by(LearningRefreshDelivery.created_at, LearningRefreshDelivery.id)
                if exclude_delivery_ids:
                    candidates = candidates.filter(~LearningRefreshDelivery.id.in_(tuple(exclude_delivery_ids)))
                delivery = candidates.with_for_update(skip_locked=True).first()
            if delivery is None:
                return LearningRefreshDeliveryResult("NO_WORK", None, company_id, None)
            if delivery.state == "completed" or (delivery.state == "processing" and delivery.lease_expires_at and delivery.lease_expires_at > now):
                return LearningRefreshDeliveryResult("NO_WORK", delivery.id, company_id, delivery.learning_evidence_id,
                    state=delivery.state, attempt_count=delivery.attempt_count)
            if delivery.attempt_count >= self._max_attempts and delivery.state == "failed":
                return LearningRefreshDeliveryResult("FAILED_TERMINAL", delivery.id, company_id, delivery.learning_evidence_id,
                    state=delivery.state, attempt_count=delivery.attempt_count, failure_code=delivery.failure_code)
            delivery.state = "processing"; delivery.attempt_count += 1; delivery.worker_id = worker_id; delivery.claim_token = uuid7()
            delivery.claimed_at = now; delivery.heartbeat_at = now; delivery.lease_expires_at = now + timedelta(seconds=self._lease_seconds)
            delivery.failure_code = delivery.failure_reason = None; delivery.row_version += 1
            s.commit()
            return LearningRefreshDeliveryResult("CLAIMED", delivery.id, company_id, delivery.learning_evidence_id,
                delivery.claim_token, delivery.attempt_count, delivery.state)
        except Exception:
            s.rollback(); raise
        finally:
            s.close()

    def heartbeat(self, company_id, delivery_id, claim_token):
        return self._owned_update(company_id, delivery_id, claim_token, "heartbeat")

    def complete(self, company_id, delivery_id, claim_token, outcome):
        return self._owned_update(company_id, delivery_id, claim_token, "complete", outcome=outcome)

    def fail(self, company_id, delivery_id, claim_token, exc, *, retryable=True):
        return self._owned_update(company_id, delivery_id, claim_token, "fail", exc=exc, retryable=retryable)

    def _owned_update(self, company_id, delivery_id, token, operation, *, outcome=None, exc=None, retryable=True):
        s = self._sf(); now = self._now()
        try:
            row = s.query(LearningRefreshDelivery).filter_by(id=delivery_id, company_id=company_id).with_for_update().one_or_none()
            if row is None or row.state != "processing" or row.claim_token != token or row.lease_expires_at <= now:
                raise LearningRefreshDeliveryLeaseError("INACTIVE_DELIVERY_LEASE")
            if operation == "heartbeat":
                row.heartbeat_at = now; row.lease_expires_at = now + timedelta(seconds=self._lease_seconds); row.row_version += 1
                status = "HEARTBEAT"
            elif operation == "complete":
                row.state = "completed"; row.processed_at = now; row.last_outcome = outcome; row.lease_expires_at = now
                row.claim_token = None; row.row_version += 1; status = "COMPLETED"
            else:
                terminal = not retryable or row.attempt_count >= self._max_attempts
                row.state = "failed" if terminal else "pending"; row.failure_code = type(exc).__name__; row.failure_reason = str(exc)[:512]
                row.lease_expires_at = now; row.claim_token = None; row.row_version += 1
                status = "FAILED_TERMINAL" if terminal else "RETRY_PENDING"
            s.commit()
            return LearningRefreshDeliveryResult(status, row.id, company_id, row.learning_evidence_id,
                attempt_count=row.attempt_count, state=row.state, failure_code=row.failure_code)
        except Exception:
            s.rollback(); raise
        finally:
            s.close()

    def process_claimed(self, company_id, delivery_id, claim_token):
        """Explicit worker step; routing remains entirely owned by B4A orchestrator."""
        # Establish current lease ownership before any projection can be routed.
        # A stale process must not even invoke the idempotent orchestrator.
        self.heartbeat(company_id, delivery_id, claim_token)
        started = perf_counter(); delivery = self.get(company_id, delivery_id)
        if delivery is None:
            raise LearningRefreshDeliveryLeaseError("DELIVERY_NOT_FOUND")
        try:
            outcome = self._orchestrator_factory().orchestrate(company_id, delivery.learning_evidence_id)
            if outcome.outcome != "COMPLETED":
                exc = RuntimeError(outcome.failure_code or outcome.failure_stage or "ORCHESTRATION_FAILED")
                retryable = outcome.failure_code not in {"LearningEvidenceNotFound", "LearningEvidenceTenantViolation", "LearningRefreshRoutingError"}
                return self.fail(company_id, delivery_id, claim_token, exc, retryable=retryable)
            summary = {"event_type": outcome.event_type, "pattern_status": outcome.pattern_status,
                       "company_status": outcome.company_status, "event_statuses": list(outcome.event_statuses),
                       "event_memory_ids": [str(x) if x else None for x in outcome.event_memory_ids],
                       "duration_ms": round((perf_counter() - started) * 1000, 3)}
            return self.complete(company_id, delivery_id, claim_token, summary)
        except (LearningEvidenceNotFound, LearningEvidenceTenantViolation, LearningRefreshRoutingError) as exc:
            return self.fail(company_id, delivery_id, claim_token, exc, retryable=False)
        except Exception as exc:
            return self.fail(company_id, delivery_id, claim_token, exc, retryable=True)
