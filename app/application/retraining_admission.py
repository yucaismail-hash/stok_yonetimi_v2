"""Explicit, PostgreSQL-backed admission controls for durable retraining jobs.

This module deliberately does not discover jobs or invoke training.  Callers
submit an already-created Tier-3 job and receive a durable cooldown/priority
decision plus, when capacity permits, a lease on the retraining lane.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os

from sqlalchemy import text
from uuid_extensions import uuid7

from app.database import SessionLocal
from app.models.retraining_job import RetrainingJob
from app.models.retraining_resource_lease import RetrainingResourceLease


COOLDOWN_POLICY_VERSION = "retraining_cooldown_v1"
PRIORITY_POLICY_VERSION = "retraining_priority_v1"
ADMISSION_POLICY_VERSION = "retraining_resource_admission_v1"
# Operationally safe default: serial retraining unless deployment configuration
# explicitly allocates more background capacity.  It is not a business policy.
DEFAULT_RETRAINING_CAPACITY = int(os.getenv("RETRAINING_GLOBAL_CAPACITY", "1"))
DEFAULT_RETRAINING_LEASE_SECONDS = int(os.getenv("RETRAINING_RESOURCE_LEASE_SECONDS", "900"))
_GLOBAL_RETRAINING_ADVISORY_LOCK = 3040404


class RetrainingResourceLeaseError(ValueError):
    """Raised when an owner attempts to operate on a stale resource lease."""


@dataclass(frozen=True)
class RetrainingAdmissionResult:
    status: str
    job_id: object
    priority_score: Decimal | None
    cooldown_until: datetime | None
    reason_code: str
    resource_lease_id: object | None = None
    resource_lease_token: object | None = None


class RetrainingCooldownPolicy:
    """Versioned cooldown policy; disabled unless a duration is configured."""

    version = COOLDOWN_POLICY_VERSION

    def __init__(self, cooldown_seconds=None, severe_drift_override=False):
        if cooldown_seconds is not None and cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        self.cooldown_seconds = cooldown_seconds
        # Hook retained deliberately; B4 has no supported severity thresholds.
        self.severe_drift_override = severe_drift_override

    def evaluate(self, session, job, now):
        previous = session.query(RetrainingJob).filter(
            RetrainingJob.company_id == job.company_id,
            RetrainingJob.material_code == job.material_code,
            RetrainingJob.demand_type == job.demand_type,
            RetrainingJob.id != job.id,
            RetrainingJob.state == "trained",
            RetrainingJob.completed_at.isnot(None),
            RetrainingJob.is_deleted.is_(False),
        ).order_by(RetrainingJob.completed_at.desc(), RetrainingJob.id.desc()).first()
        if self.cooldown_seconds is None:
            return "ELIGIBLE_NOW", None, "NO_CONFIGURED_COOLDOWN"
        if previous is None:
            return "ELIGIBLE_NOW", None, "NO_PREVIOUS_SUCCESSFUL_TRAINING"
        until = previous.completed_at + timedelta(seconds=self.cooldown_seconds)
        if now < until:
            return "COOLDOWN", until, "SUCCESSFUL_TRAINING_COOLDOWN"
        return "ELIGIBLE_NOW", until, "COOLDOWN_EXPIRED"


class RetrainingPriorityPolicy:
    """Deterministic evidence-only ordering for explicitly submitted jobs."""

    version = PRIORITY_POLICY_VERSION

    @staticmethod
    def score(job):
        signal_count = int(bool(job.performance_drift)) + int(bool(job.demand_drift))
        deterioration = max(Decimal("0"), Decimal(str(job.current_wape or 0)) - Decimal(str(job.baseline_wape or 0)))
        # Values are evidence rankings, not unsupported business/revenue weights.
        return (
            Decimal("1000")
            + Decimal(signal_count * 100)
            + min(Decimal(max(job.sample_count, 0)), Decimal("100"))
            + (deterioration * Decimal("1000"))
        )


class RetrainingAdmissionService:
    """Admission boundary. PostgreSQL advisory locking makes capacity global."""

    def __init__(self, session_factory=SessionLocal, *, cooldown_seconds=None,
                 capacity=DEFAULT_RETRAINING_CAPACITY,
                 lease_seconds=DEFAULT_RETRAINING_LEASE_SECONDS, now_factory=None):
        if capacity < 1:
            raise ValueError("retraining capacity must be positive")
        if lease_seconds < 1:
            raise ValueError("retraining resource lease_seconds must be positive")
        self._session_factory = session_factory
        self._cooldown = RetrainingCooldownPolicy(cooldown_seconds)
        self._capacity = capacity
        self._lease_seconds = lease_seconds
        self._now = now_factory or (lambda: datetime.now(timezone.utc))

    def evaluate(self, company_id, job_id) -> RetrainingAdmissionResult:
        """Persist cooldown and priority only; never reserves capacity."""
        session = self._session_factory()
        try:
            job = self._job_for_update(session, company_id, job_id)
            result = self._evaluate_locked(session, job, self._now())
            job.admission_policy_version = ADMISSION_POLICY_VERSION
            job.admission_result = result.status
            job.admission_reason_code = result.reason_code
            job.admission_decided_at = self._now()
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def admit(self, company_id, job_id, worker_id="retraining_admission") -> RetrainingAdmissionResult:
        """Evaluate then atomically acquire one global retraining lease if possible."""
        session = self._session_factory()
        try:
            job = self._job_for_update(session, company_id, job_id)
            now = self._now()
            decision = self._evaluate_locked(session, job, now)
            if decision.status == "COOLDOWN":
                self._record_admission(job, decision.status, decision.reason_code, now)
                session.commit()
                return decision
            self._global_lock(session)
            self._expire_leases(session, now)
            existing = session.query(RetrainingResourceLease).filter_by(
                retraining_job_id=job.id, company_id=company_id, active=True
            ).with_for_update().one_or_none()
            if existing is not None:
                self._record_admission(job, "ADMITTED", "ALREADY_ADMITTED", now)
                session.commit()
                return RetrainingAdmissionResult("ADMITTED", job.id, decision.priority_score, decision.cooldown_until,
                                                "ALREADY_ADMITTED", existing.id, existing.lease_token)
            active_count = session.query(RetrainingResourceLease).filter_by(active=True).count()
            if active_count >= self._capacity:
                self._record_admission(job, "CAPACITY_BLOCKED", "GLOBAL_RETRAINING_CAPACITY_REACHED", now)
                session.commit()
                return RetrainingAdmissionResult("CAPACITY_BLOCKED", job.id, decision.priority_score,
                                                decision.cooldown_until, "GLOBAL_RETRAINING_CAPACITY_REACHED")
            lease = self._new_lease(job, worker_id, now)
            session.add(lease)
            self._record_admission(job, "ADMITTED", "GLOBAL_RETRAINING_SLOT_ACQUIRED", now)
            session.commit()
            return RetrainingAdmissionResult("ADMITTED", job.id, decision.priority_score, decision.cooldown_until,
                                            "GLOBAL_RETRAINING_SLOT_ACQUIRED", lease.id, lease.lease_token)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ranked(self, company_id, job_ids):
        """Explicit caller-supplied queue ordering; this is not a scanner."""
        decisions = [self.evaluate(company_id, job_id) for job_id in job_ids]
        session = self._session_factory()
        try:
            created = {
                row.id: row.created_at
                for row in session.query(RetrainingJob.id, RetrainingJob.created_at).filter(
                    RetrainingJob.company_id == company_id, RetrainingJob.id.in_(job_ids)
                )
            }
        finally:
            session.close()
        return sorted(decisions, key=lambda row: (-row.priority_score, created[row.job_id], str(row.job_id)))

    def heartbeat(self, company_id, job_id, lease_token):
        session = self._session_factory()
        try:
            self._global_lock(session)
            now = self._now()
            lease = session.query(RetrainingResourceLease).filter_by(
                company_id=company_id, retraining_job_id=job_id, active=True
            ).with_for_update().one_or_none()
            if lease is None or lease.lease_token != lease_token or lease.lease_expires_at <= now:
                raise RetrainingResourceLeaseError("inactive or stale retraining resource lease")
            lease.heartbeat_at = now
            lease.lease_expires_at = now + timedelta(seconds=self._lease_seconds)
            session.commit()
            return lease
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def release(self, company_id, job_id, lease_token, reason_code="TERMINAL"):
        session = self._session_factory()
        try:
            self._global_lock(session)
            now = self._now()
            lease = session.query(RetrainingResourceLease).filter_by(
                company_id=company_id, retraining_job_id=job_id, active=True
            ).with_for_update().one_or_none()
            if lease is None or lease.lease_token != lease_token or lease.lease_expires_at <= now:
                raise RetrainingResourceLeaseError("inactive or stale retraining resource lease")
            lease.active = False
            lease.released_at = now
            lease.release_reason_code = reason_code
            session.commit()
            return lease
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def active_lease(self, company_id, job_id):
        session = self._session_factory()
        try:
            now = self._now()
            return session.query(RetrainingResourceLease).filter(
                RetrainingResourceLease.company_id == company_id,
                RetrainingResourceLease.retraining_job_id == job_id,
                RetrainingResourceLease.active.is_(True),
                RetrainingResourceLease.lease_expires_at > now,
            ).one_or_none()
        finally:
            session.close()

    @staticmethod
    def _global_lock(session):
        session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": _GLOBAL_RETRAINING_ADVISORY_LOCK})

    @staticmethod
    def _job_for_update(session, company_id, job_id):
        job = session.query(RetrainingJob).filter_by(
            id=job_id, company_id=company_id, is_deleted=False
        ).with_for_update().one_or_none()
        if job is None:
            raise ValueError("RETRAINING_JOB_NOT_FOUND")
        if job.state in ("trained", "not_trainable", "failed"):
            raise ValueError("RETRAINING_JOB_TERMINAL")
        return job

    def _evaluate_locked(self, session, job, now):
        status, cooldown_until, reason = self._cooldown.evaluate(session, job, now)
        score = RetrainingPriorityPolicy.score(job)
        job.cooldown_policy_version = self._cooldown.version
        job.cooldown_decision_at = now
        job.cooldown_until = cooldown_until
        job.cooldown_reason_code = reason
        job.priority_policy_version = PRIORITY_POLICY_VERSION
        job.priority_score = score
        job.priority_calculated_at = now
        return RetrainingAdmissionResult(status, job.id, score, cooldown_until, reason)

    @staticmethod
    def _record_admission(job, status, reason, now):
        job.admission_policy_version = ADMISSION_POLICY_VERSION
        job.admission_result = status
        job.admission_reason_code = reason
        job.admission_decided_at = now

    def _new_lease(self, job, worker_id, now):
        return RetrainingResourceLease(
            company_id=job.company_id, retraining_job_id=job.id, worker_id=worker_id,
            lease_token=uuid7(), claimed_at=now, heartbeat_at=now,
            lease_expires_at=now + timedelta(seconds=self._lease_seconds), active=True,
        )

    @staticmethod
    def _expire_leases(session, now):
        session.query(RetrainingResourceLease).filter(
            RetrainingResourceLease.active.is_(True),
            RetrainingResourceLease.lease_expires_at <= now,
        ).update({
            "active": False,
            "released_at": now,
            "release_reason_code": "LEASE_EXPIRED",
        }, synchronize_session=False)
