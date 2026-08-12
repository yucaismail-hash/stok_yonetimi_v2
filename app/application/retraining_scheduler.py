"""Durable, callable ownership boundary for periodic retraining scanner ticks.

There is intentionally no timer, cron registration, startup hook, or loop in
this module.  An infrastructure scheduler may call ``run_tick`` on cadence.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

from sqlalchemy.exc import IntegrityError

from app.application.retraining_scanner import RetrainingScannerService
from app.database import SessionLocal
from app.models.retraining_scheduler_tick import RetrainingSchedulerTick
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


SCHEDULER_POLICY_VERSION = "retraining_periodic_tick_v1"


@dataclass(frozen=True)
class RetrainingSchedulerTickResult:
    status: str
    tick_id: object
    tick_identity: str
    scheduled_bucket_at: datetime
    activation_report: object | None = None
    failure_code: str | None = None


class RetrainingScannerSchedulerService:
    """Acquires one durable tick owner, then delegates all work to B5B."""

    def __init__(self, session_factory=SessionLocal, scanner_factory=RetrainingScannerService,
                 *, policy_version=SCHEDULER_POLICY_VERSION, lease_seconds=900, now_factory=None,
                 cooldown_seconds=None, capacity=None):
        if lease_seconds < 1:
            raise ValueError("scheduler tick lease_seconds must be positive")
        self._session_factory = session_factory
        self._scanner_factory = scanner_factory
        self._policy_version = policy_version
        self._lease_seconds = lease_seconds
        self._now = now_factory or (lambda: datetime.now(timezone.utc))
        self._cooldown_seconds = cooldown_seconds
        self._capacity = capacity

    def run_tick(self, company_id, start_period, end_period, *, scheduled_for, cadence_seconds,
                 owner_id="retraining_scheduler", material_codes=None, demand_type=None,
                 last_seen_evaluation_ids=None):
        """Run at most one effective company/window cadence bucket.

        A restart resumes future buckets by calling this method with a new
        ``scheduled_for``.  Failed buckets remain audited and are not retried
        immediately; callers may choose one explicit bounded catch-up tick.
        """
        start = parse_weekly_period(start_period).period
        end = parse_weekly_period(end_period).period
        if cadence_seconds < 1:
            raise ValueError("cadence_seconds must be positive")
        if start > end:
            raise ValueError("start_period must not be after end_period")
        bucket = self._bucket(scheduled_for, cadence_seconds)
        material_scope = sorted(set(material_codes)) if material_codes is not None else None
        normalized_demand = validate_demand_type(demand_type) if demand_type is not None else None
        identity = self._identity(company_id, start, end, bucket, cadence_seconds, material_scope, normalized_demand)
        acquired = self._acquire(company_id, identity, bucket, cadence_seconds, start, end, material_scope, normalized_demand, owner_id)
        if acquired.status != "ACQUIRED":
            return acquired
        try:
            scanner = self._scanner_factory(
                self._session_factory, cooldown_seconds=self._cooldown_seconds,
                **({"capacity": self._capacity} if self._capacity is not None else {}),
            )
            report = scanner.scan_and_activate(
                company_id, start, end, worker_id=owner_id, material_codes=material_scope,
                demand_type=normalized_demand, last_seen_evaluation_ids=last_seen_evaluation_ids,
            )
            self._complete(company_id, acquired.tick_id, owner_id, report)
            return RetrainingSchedulerTickResult("COMPLETED", acquired.tick_id, identity, bucket, report)
        except Exception as exc:
            self._fail(company_id, acquired.tick_id, owner_id, exc)
            return RetrainingSchedulerTickResult("FAILED", acquired.tick_id, identity, bucket, None, type(exc).__name__)

    def _acquire(self, company_id, identity, bucket, cadence_seconds, start, end, material_scope, demand_type, owner_id):
        session = self._session_factory()
        now = self._now()
        try:
            tick = session.query(RetrainingSchedulerTick).filter_by(
                company_id=company_id, tick_identity=identity,
            ).with_for_update().one_or_none()
            if tick is not None:
                if tick.state == "completed":
                    return RetrainingSchedulerTickResult("ALREADY_COMPLETED", tick.id, identity, bucket)
                if tick.state == "failed":
                    return RetrainingSchedulerTickResult("FAILED_PREVIOUSLY", tick.id, identity, bucket, failure_code=tick.failure_code)
                if tick.lease_expires_at and tick.lease_expires_at > now:
                    return RetrainingSchedulerTickResult("ALREADY_RUNNING", tick.id, identity, bucket)
                self._claim(tick, owner_id, now)
                session.commit()
                return RetrainingSchedulerTickResult("ACQUIRED", tick.id, identity, bucket)
            tick = RetrainingSchedulerTick(
                company_id=company_id, tick_identity=identity, scheduler_policy_version=self._policy_version,
                scheduled_bucket_at=bucket, cadence_seconds=str(cadence_seconds), start_period=start, end_period=end,
                material_scope=material_scope, demand_type_scope=demand_type, state="running",
            )
            self._claim(tick, owner_id, now)
            session.add(tick)
            try:
                session.commit()
                return RetrainingSchedulerTickResult("ACQUIRED", tick.id, identity, bucket)
            except IntegrityError:
                session.rollback()
                existing = session.query(RetrainingSchedulerTick).filter_by(company_id=company_id, tick_identity=identity).one()
                status = "ALREADY_COMPLETED" if existing.state == "completed" else "ALREADY_RUNNING" if existing.state == "running" else "FAILED_PREVIOUSLY"
                return RetrainingSchedulerTickResult(status, existing.id, identity, bucket, failure_code=existing.failure_code)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _complete(self, company_id, tick_id, owner_id, report):
        session = self._session_factory()
        try:
            tick = session.query(RetrainingSchedulerTick).filter_by(id=tick_id, company_id=company_id).with_for_update().one()
            if tick.state != "running" or tick.owner_id != owner_id:
                return
            tick.state = "completed"; tick.completed_at = self._now(); tick.lease_expires_at = tick.completed_at
            tick.report_summary = {"tier3_count": report.scan_report.tier3_count, "jobs_created": report.scan_report.jobs_created,
                                   "jobs_existing": report.scan_report.jobs_existing, "activated": len(report.activated), "errors": len(report.errors)}
            session.commit()
        finally:
            session.close()

    def _fail(self, company_id, tick_id, owner_id, exc):
        session = self._session_factory()
        try:
            tick = session.query(RetrainingSchedulerTick).filter_by(id=tick_id, company_id=company_id).with_for_update().one()
            if tick.state == "running" and tick.owner_id == owner_id:
                tick.state = "failed"; tick.completed_at = self._now(); tick.lease_expires_at = tick.completed_at
                tick.failure_code = type(exc).__name__; tick.failure_reason = str(exc)[:512]
                session.commit()
        finally:
            session.close()

    def _claim(self, tick, owner_id, now):
        tick.state = "running"; tick.owner_id = owner_id; tick.claimed_at = now
        tick.lease_expires_at = now + timedelta(seconds=self._lease_seconds)
        tick.completed_at = None; tick.failure_code = None; tick.failure_reason = None

    def _identity(self, company_id, start, end, bucket, cadence, materials, demand):
        payload = {"company_id": str(company_id), "start_period": start, "end_period": end,
                   "policy_version": self._policy_version, "scheduled_bucket_at": bucket.isoformat(),
                   "cadence_seconds": cadence, "material_scope": materials, "demand_type_scope": demand}
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _bucket(scheduled_for, cadence_seconds):
        if scheduled_for.tzinfo is None:
            raise ValueError("scheduled_for must be timezone-aware")
        utc = scheduled_for.astimezone(timezone.utc)
        epoch = int(utc.timestamp())
        return datetime.fromtimestamp(epoch - (epoch % cadence_seconds), timezone.utc)
