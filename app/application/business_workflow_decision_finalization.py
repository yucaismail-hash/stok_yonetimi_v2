"""Crash-safe advisory Decision finalization for completed Business Workflows."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from uuid_extensions import uuid7

from app.application.business_decision_plan import BusinessDecisionPlanService
from app.application.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReferenceService
from app.database import SessionLocal
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.runtime import RuntimeExecution, RuntimeResultReference


class DecisionFinalizationError(RuntimeError):
    pass


@dataclass(frozen=True)
class DecisionFinalizationClaim:
    finalization_id: object
    company_id: object
    execution_id: object
    lease_token: object
    aggregate_result_reference_id: object


@dataclass(frozen=True)
class DecisionFinalizationResult:
    finalization_id: object
    status: str
    claimed: bool
    attempt_count: int
    completed_material_codes: tuple[str, ...]
    limitations: tuple[dict, ...]


class BusinessWorkflowDecisionFinalizationService:
    """Owns only advisory lifecycle state, never analytical workflow state."""

    _CLAIMABLE = {"pending", "failed", "partially_succeeded"}

    def __init__(self, session_factory=SessionLocal, plan_service_factory=None, reference_service_factory=None, lease_seconds=300):
        self._sf = session_factory
        self._plan_service_factory = plan_service_factory or BusinessDecisionPlanService
        self._reference_service_factory = reference_service_factory or BusinessWorkflowDecisionSnapshotReferenceService
        self._lease_seconds = lease_seconds

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    @staticmethod
    def _safe_limitations(limitations):
        """Persist bounded operational facts, never tracebacks or candidate payloads."""
        out = []
        for item in limitations or ():
            if not isinstance(item, dict):
                continue
            out.append({
                "material_code": str(item.get("material_code", ""))[:128],
                "code": str(item.get("code", "DECISION_LIMITED"))[:64],
                "failure_stage": str(item.get("failure_stage", "unknown"))[:64],
                "error_class": str(item.get("error_class", "DecisionFinalizationError"))[:128],
            })
        return out

    @staticmethod
    def _safe_error(exc):
        return {
            "code": "DECISION_FINALIZATION_FAILED",
            "error_class": type(exc).__name__[:128],
            "message": "Decision finalization did not complete; retry from persisted analytical evidence.",
        }

    def ensure(self, company_id, execution_id):
        """Create state only after the completed analytical aggregate is durable."""
        session = self._sf()
        try:
            execution = session.query(RuntimeExecution).filter_by(
                execution_id=execution_id, company_id=company_id, analysis_type="business_workflow", state="completed"
            ).one_or_none()
            if execution is None or float(execution.progress) != 100:
                raise DecisionFinalizationError("completed analytical Business Workflow is unavailable")
            aggregate = session.query(RuntimeResultReference).filter_by(
                execution_id=execution_id, company_id=company_id, runtime_task_id=None,
                result_type="business_workflow", validation_status="validated"
            ).one_or_none()
            if aggregate is None:
                raise DecisionFinalizationError("completed Business Workflow aggregate is unavailable")
            existing = session.query(BusinessWorkflowDecisionFinalization).filter_by(
                company_id=company_id, execution_id=execution_id
            ).one_or_none()
            if existing is not None:
                if existing.aggregate_result_reference_id != aggregate.id:
                    raise DecisionFinalizationError("finalization aggregate reference does not match authoritative workflow aggregate")
                return existing.id
            row = BusinessWorkflowDecisionFinalization(
                company_id=company_id,
                execution_id=execution_id,
                aggregate_result_reference_id=aggregate.id,
                status="pending",
                completed_material_codes=[],
                limitations=[],
            )
            session.add(row)
            session.commit()
            return row.id
        except IntegrityError:
            session.rollback()
            existing = session.query(BusinessWorkflowDecisionFinalization).filter_by(
                company_id=company_id, execution_id=execution_id
            ).one()
            return existing.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def claim(self, company_id, execution_id):
        session = self._sf()
        try:
            row = session.query(BusinessWorkflowDecisionFinalization).filter_by(
                company_id=company_id, execution_id=execution_id
            ).with_for_update().one_or_none()
            if row is None:
                return None
            now = self._now()
            expired = row.status == "running" and row.lease_expires_at is not None and row.lease_expires_at <= now
            if row.status == "succeeded" or (row.status == "running" and not expired):
                return None
            if row.status not in self._CLAIMABLE and not expired:
                return None
            token = uuid7()
            row.status = "running"
            row.attempt_count += 1
            row.row_version += 1
            row.lease_token = token
            row.lease_expires_at = now + timedelta(seconds=self._lease_seconds)
            row.last_error = None
            session.commit()
            return DecisionFinalizationClaim(row.id, company_id, execution_id, token, row.aggregate_result_reference_id)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _finish(self, claim, plan=None, error=None):
        session = self._sf()
        try:
            row = session.query(BusinessWorkflowDecisionFinalization).filter_by(
                id=claim.finalization_id, company_id=claim.company_id, execution_id=claim.execution_id
            ).with_for_update().one_or_none()
            now = self._now()
            if row is None or row.status != "running" or row.lease_token != claim.lease_token or row.lease_expires_at is None or row.lease_expires_at <= now:
                raise DecisionFinalizationError("Decision finalization lease is no longer owned")
            if error is not None:
                row.status = "failed"
                row.last_error = self._safe_error(error)
                row.limitations = []
                row.completed_material_codes = []
                row.finalized_at = now
            else:
                completed = tuple(sorted({str(item["material_code"]) for item in plan.items if item.get("material_code")}))
                limitations = self._safe_limitations(plan.limitations)
                row.completed_material_codes = list(completed)
                row.limitations = limitations
                row.last_error = None
                row.status = "partially_succeeded" if completed and limitations else ("failed" if limitations else "succeeded")
                row.finalized_at = now
            row.lease_token = None
            row.lease_expires_at = None
            row.row_version += 1
            session.commit()
            return DecisionFinalizationResult(row.id, row.status, True, row.attempt_count, tuple(row.completed_material_codes), tuple(row.limitations))
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def finalize(self, company_id, execution_id):
        """Ensure, claim, and materialize from persisted analytics without rerunning it."""
        self.ensure(company_id, execution_id)
        claim = self.claim(company_id, execution_id)
        if claim is None:
            session = self._sf()
            try:
                row = session.query(BusinessWorkflowDecisionFinalization).filter_by(company_id=company_id, execution_id=execution_id).one()
                return DecisionFinalizationResult(row.id, row.status, False, row.attempt_count, tuple(row.completed_material_codes or ()), tuple(row.limitations or ()))
            finally:
                session.close()
        try:
            plan = self._plan_service_factory().materialize(company_id, execution_id)
        except Exception as exc:
            return self._finish(claim, error=exc)
        try:
            # Each successfully materialized Snapshot receives execution-local,
            # immutable provenance before the lifecycle can report success.
            self._reference_service_factory().ensure_for_plan(company_id, execution_id, claim.finalization_id, plan)
        except Exception as exc:
            return self._finish(claim, error=exc)
        return self._finish(claim, plan=plan)

    def recover_due(self, company_id, limit=25):
        """Bounded fresh-process recovery; callers supply tenant authority explicitly."""
        session = self._sf()
        try:
            now = self._now()
            rows = session.query(BusinessWorkflowDecisionFinalization).filter(
                BusinessWorkflowDecisionFinalization.company_id == company_id,
                ((BusinessWorkflowDecisionFinalization.status.in_(self._CLAIMABLE)) |
                 ((BusinessWorkflowDecisionFinalization.status == "running") & (BusinessWorkflowDecisionFinalization.lease_expires_at <= now)))
            ).order_by(BusinessWorkflowDecisionFinalization.created_at, BusinessWorkflowDecisionFinalization.id).limit(limit).all()
            execution_ids = tuple(row.execution_id for row in rows)
        finally:
            session.close()
        return tuple(self.finalize(company_id, execution_id) for execution_id in execution_ids)
