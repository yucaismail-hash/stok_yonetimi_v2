"""Explicit leased execution of one durable Tier-3 RetrainingJob."""

from dataclasses import dataclass
from datetime import datetime, timezone

from uuid_extensions import uuid7

from app.application.xgboost_challenger_artifacts import ArtifactIntegrityError, XGBoostChallengerArtifactService
from app.application.xgboost_challenger_training import XGBoostChallengerTrainingRequest, XGBoostChallengerTrainingService
from app.application.retraining_admission import DEFAULT_RETRAINING_CAPACITY, RetrainingAdmissionService, RetrainingResourceLeaseError
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore, RuntimeStoreConcurrencyError
from app.models.forecast_evaluation import ForecastEvaluationPoint
from app.models.forecast_vintage import ForecastVintage
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution


RETRAINING_TASK_ID = "xgboost_challenger_train"
RETRAINING_CAPABILITY = "xgboost_challenger_training"
RETRAINING_MAX_ATTEMPTS = 2
RETRAINING_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class RetrainingExecutionStart:
    status: str
    runtime_execution_id: object | None
    runtime_task_id: object | None


@dataclass(frozen=True)
class RetrainingWorkerResult:
    status: str
    job_id: object | None
    runtime_execution_id: object | None
    task_id: object | None
    attempt_number: int | None
    artifact_id: object | None = None
    failure_code: str | None = None


class RetrainingExecutionService:
    """Explicitly starts one pending Tier-3 job; it never scans or auto-starts jobs."""

    def __init__(self, session_factory=SessionLocal, admission_service_factory=RetrainingAdmissionService,
                 cooldown_seconds=None, capacity=DEFAULT_RETRAINING_CAPACITY):
        self._session_factory = session_factory
        self._admission_service_factory = admission_service_factory
        self._cooldown_seconds = cooldown_seconds
        self._capacity = capacity

    def start(self, company_id, retraining_job_id, worker_id="retraining_admission") -> RetrainingExecutionStart:
        # The admission decision is persisted before creating the runtime. It is
        # explicit caller-driven, never a periodic scan.
        admission = self._admission_service_factory(
            self._session_factory, cooldown_seconds=self._cooldown_seconds, capacity=self._capacity,
        )
        session = self._session_factory()
        try:
            existing = session.query(RetrainingJob).filter_by(id=retraining_job_id, company_id=company_id, is_deleted=False).one_or_none()
            if existing is None:
                return RetrainingExecutionStart("NOT_EXECUTABLE", None, None)
            if existing.runtime_execution_id is not None:
                task = session.query(__import__("app.models.runtime", fromlist=["RuntimeTask"]).RuntimeTask).filter_by(
                    execution_id=existing.runtime_execution_id, company_id=company_id, task_id=RETRAINING_TASK_ID,
                ).one_or_none()
                status = "ALREADY_COMPLETED" if existing.state in ("trained", "not_trainable", "failed") else "ALREADY_STARTED"
                return RetrainingExecutionStart(status, existing.runtime_execution_id, task.id if task else None)
            if existing.state != "pending" or existing.eligibility_tier != "TIER_3_DEEP_LEARN_RETRAIN" or existing.eligibility_action != "RETRAIN_ELIGIBLE":
                return RetrainingExecutionStart("NOT_EXECUTABLE", None, None)
        finally:
            session.close()
        admission_result = admission.admit(company_id, retraining_job_id, worker_id)
        if admission_result.status != "ADMITTED":
            return RetrainingExecutionStart(admission_result.status, None, None)
        session = self._session_factory()
        try:
            job = session.query(RetrainingJob).filter_by(id=retraining_job_id, company_id=company_id, is_deleted=False).with_for_update().one_or_none()
            if job is None:
                return RetrainingExecutionStart("NOT_EXECUTABLE", None, None)
            if job.runtime_execution_id is not None:
                task = session.query(__import__("app.models.runtime", fromlist=["RuntimeTask"]).RuntimeTask).filter_by(
                    execution_id=job.runtime_execution_id, company_id=company_id, task_id=RETRAINING_TASK_ID,
                ).one_or_none()
                status = "ALREADY_COMPLETED" if job.state in ("trained", "not_trainable", "failed") else "ALREADY_STARTED"
                return RetrainingExecutionStart(status, job.runtime_execution_id, task.id if task else None)
            if job.state != "pending" or job.eligibility_tier != "TIER_3_DEEP_LEARN_RETRAIN" or job.eligibility_action != "RETRAIN_ELIGIBLE":
                return RetrainingExecutionStart("NOT_EXECUTABLE", None, None)
            source = self._source_execution(session, job)
            execution = RuntimeExecution(
                execution_id=uuid7(), company_id=company_id, user_id=source.user_id, dataset_id=source.dataset_id,
                workflow_id="retraining-" + str(job.id), analysis_type="retraining", state="queued", current_stage="retraining",
                progress=0, idempotency_key="retraining:" + job.candidate_fingerprint, accepted_at=datetime.now(timezone.utc),
                queued_at=datetime.now(timezone.utc), contract_version="1.0.0",
                metadata_={"retraining_job_id": str(job.id), "material_code": job.material_code, "demand_type": job.demand_type,
                           "training_cutoff_period": job.training_cutoff_period, "candidate_fingerprint": job.candidate_fingerprint,
                           "latest_evaluation_id": str(job.latest_evaluation_id)},
            )
            task_rows = [{
                "workflow_id": execution.workflow_id, "task_id": RETRAINING_TASK_ID, "capability": RETRAINING_CAPABILITY,
                "task_order": 0, "required": True, "skippable": False, "dependencies": [], "state": "pending",
                "max_attempts": RETRAINING_MAX_ATTEMPTS, "timeout_seconds": RETRAINING_TIMEOUT_SECONDS,
                "metrics": {"retraining_job_id": str(job.id), "material_code": job.material_code, "demand_type": job.demand_type,
                            "training_cutoff_period": job.training_cutoff_period, "candidate_fingerprint": job.candidate_fingerprint,
                            "latest_evaluation_id": str(job.latest_evaluation_id)},
            }]
            store = RuntimeStore(session)
            stored = store.create_execution(execution, task_rows)
            task = store.get_tasks(stored.execution_id, company_id)[0]
            job.runtime_execution_id = stored.execution_id
            job.state = "queued"
            session.commit()
            return RetrainingExecutionStart("STARTED", stored.execution_id, task.id)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _source_execution(session, job):
        point = session.query(ForecastEvaluationPoint).filter_by(
            evaluation_id=job.latest_evaluation_id, material_code=job.material_code,
        ).order_by(ForecastEvaluationPoint.target_period).first()
        if point is None:
            raise ValueError("RETRAINING_SOURCE_EVIDENCE_UNAVAILABLE")
        vintage = session.query(ForecastVintage).filter_by(id=point.forecast_vintage_id, company_id=job.company_id).one_or_none()
        if vintage is None:
            raise ValueError("RETRAINING_SOURCE_VINTAGE_UNAVAILABLE")
        source = session.query(RuntimeExecution).filter_by(execution_id=vintage.execution_id, company_id=job.company_id).one_or_none()
        if source is None:
            raise ValueError("RETRAINING_SOURCE_EXECUTION_UNAVAILABLE")
        return source


class RetrainingTrainingWorker:
    """Dedicated leased worker; only explicit callers invoke ``run``."""

    def __init__(self, session_factory=SessionLocal, worker_id="retraining_worker", lease_seconds=900, training_service_factory=None, artifact_service_factory=None, post_artifact_persisted_hook=None, admission_service_factory=RetrainingAdmissionService, capacity=DEFAULT_RETRAINING_CAPACITY):
        self._session_factory = session_factory
        self._worker_id = worker_id
        self._lease_seconds = lease_seconds
        self._training_service_factory = training_service_factory or XGBoostChallengerTrainingService
        self._artifact_service_factory = artifact_service_factory or XGBoostChallengerArtifactService
        self._post_artifact_persisted_hook = post_artifact_persisted_hook
        self._admission_service_factory = admission_service_factory
        self._capacity = capacity

    def run(self, company_id, retraining_job_id) -> RetrainingWorkerResult:
        session = self._session_factory()
        try:
            job = session.query(RetrainingJob).filter_by(id=retraining_job_id, company_id=company_id, is_deleted=False).one_or_none()
            if job is None or job.runtime_execution_id is None:
                return RetrainingWorkerResult("NO_WORK", retraining_job_id, None, None, None)
            if job.state in ("trained", "not_trainable", "failed"):
                return RetrainingWorkerResult("ALREADY_COMPLETED", job.id, job.runtime_execution_id, None, None, job.model_artifact_id, job.failure_code)
            store = RuntimeStore(session)
            execution = store.get_execution(job.runtime_execution_id, company_id)
            if execution is None:
                return RetrainingWorkerResult("NO_WORK", job.id, job.runtime_execution_id, None, None)
            if execution.state == "queued":
                try:
                    execution = store.transition_execution(execution.execution_id, company_id, "queued", "running", execution.row_version, current_stage="retraining", started_at=datetime.now(timezone.utc))
                except RuntimeStoreConcurrencyError:
                    session.rollback()
                    return RetrainingWorkerResult("NO_WORK", job.id, job.runtime_execution_id, None, None)
            task = next((row for row in store.get_tasks(execution.execution_id, company_id) if row.task_id == RETRAINING_TASK_ID), None)
            if task is None or task.capability != RETRAINING_CAPABILITY:
                raise ValueError("RETRAINING_TASK_UNAVAILABLE")
            try:
                task, attempt = store.claim_task(execution.execution_id, task.task_id, company_id, self._worker_id, self._lease_seconds, task.row_version)
            except RuntimeStoreConcurrencyError:
                session.rollback()
                return RetrainingWorkerResult("NO_WORK", job.id, job.runtime_execution_id, task.id if task else None, None)
            job.state = "running"
            job.started_at = job.started_at or datetime.now(timezone.utc)
            session.commit()
            session.refresh(job)
            resource = self._admission_service_factory(self._session_factory, capacity=self._capacity)
            resource_lease = resource.active_lease(company_id, job.id)
            if resource_lease is None:
                # No background capacity is consumed by a fit until a durable
                # resource admission exists. The task remains retryable.
                failed = store.fail_task_attempt(execution.execution_id, task.task_id, company_id, task.lease_token,
                                                 {"code": "RETRAINING_RESOURCE_UNAVAILABLE"}, retryable=True)
                job.state = "queued" if failed.state != "failed" else "failed"
                session.commit()
                return RetrainingWorkerResult("CAPACITY_BLOCKED", job.id, execution.execution_id, task.id, attempt.attempt_number)
            resource.heartbeat(company_id, job.id, resource_lease.lease_token)
            try:
                artifact_service = self._artifact_service_factory(session)
                if job.model_artifact_id is not None:
                    # An earlier worker durably wrote this marker before a crash.
                    # Reuse trusted immutable evidence instead of fitting again.
                    artifact = artifact_service.get(company_id, job.model_artifact_id)
                    artifact_service.load(company_id, artifact.id)
                    persisted = type("Persisted", (), {"artifact": artifact, "created": False})()
                    result = None
                else:
                    result = self._training_service_factory(session).train(self._request(job))
                    if result.status == "NOT_TRAINABLE":
                        payload = {"status": "NOT_TRAINABLE", "reason_code": result.reason_code, "retraining_job_id": str(job.id), "fit_count": 0}
                        store.complete_task_attempt(execution.execution_id, task.task_id, company_id, task.lease_token, "retraining", payload)
                        job.state = "not_trainable"; job.failure_code = result.reason_code; job.completed_at = datetime.now(timezone.utc)
                        session.refresh(execution)
                        store.complete_execution(execution.execution_id, company_id, execution.row_version)
                        session.commit()
                        self._release_resource(company_id, job.id, resource_lease.lease_token, "NOT_TRAINABLE")
                        return RetrainingWorkerResult("NOT_TRAINABLE", job.id, execution.execution_id, task.id, attempt.attempt_number, failure_code=result.reason_code)
                    if result.status != "TRAINED":
                        raise RuntimeError("UNEXPECTED_TRAINING_RESULT")
                    persisted = artifact_service.persist(self._request(job), result)
                    # Commit the artifact link before task/job terminalization.  This
                    # is the durable recovery marker for a crash in the final window.
                    job.model_artifact_id = persisted.artifact.id
                    session.commit()
                    session.refresh(job)
                    if self._post_artifact_persisted_hook is not None:
                        self._post_artifact_persisted_hook(job, persisted.artifact)
                    execution = store.get_execution(job.runtime_execution_id, company_id)
                    task = next(row for row in store.get_tasks(execution.execution_id, company_id) if row.task_id == RETRAINING_TASK_ID)
                payload = {"status": "TRAINED", "retraining_job_id": str(job.id), "model_artifact_id": str(persisted.artifact.id),
                           "artifact_checksum": persisted.artifact.artifact_checksum, "fit_count": 1,
                           "artifact_reused": not persisted.created,
                           "training_count": result.training_count if result is not None else persisted.artifact.training_sample_count,
                           "validation_count": result.validation_count if result is not None else persisted.artifact.validation_sample_count}
                store.complete_task_attempt(execution.execution_id, task.task_id, company_id, task.lease_token, "retraining", payload)
                job.state = "trained"; job.model_artifact_id = persisted.artifact.id; job.completed_at = datetime.now(timezone.utc)
                session.refresh(execution)
                store.complete_execution(execution.execution_id, company_id, execution.row_version)
                session.commit()
                self._release_resource(company_id, job.id, resource_lease.lease_token, "TRAINED")
                return RetrainingWorkerResult("TRAINED", job.id, execution.execution_id, task.id, attempt.attempt_number, persisted.artifact.id)
            except Exception as exc:
                error = {"code": type(exc).__name__, "message": str(exc)}
                retryable = not isinstance(exc, (ArtifactIntegrityError, ValueError))
                failed = store.fail_task_attempt(execution.execution_id, task.task_id, company_id, task.lease_token, error, retryable=retryable)
                session.refresh(execution)
                if failed.state == "failed":
                    job.state = "failed"; job.failure_code = error["code"]; job.failure_reason = error["message"]; job.completed_at = datetime.now(timezone.utc)
                    store.fail_execution(execution.execution_id, company_id, execution.row_version, error, current_stage=RETRAINING_TASK_ID)
                    session.commit()
                    self._release_resource(company_id, job.id, resource_lease.lease_token, "FAILED")
                    return RetrainingWorkerResult("FAILED", job.id, execution.execution_id, task.id, attempt.attempt_number, failure_code=error["code"])
                job.state = "queued"
                session.commit()
                return RetrainingWorkerResult("RETRY_SCHEDULED", job.id, execution.execution_id, task.id, attempt.attempt_number, failure_code=error["code"])
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _request(job):
        evidence = dict(job.eligibility_evidence or {})
        evidence["retraining_job_id"] = str(job.id)
        evidence["candidate_fingerprint"] = job.candidate_fingerprint
        evidence["latest_evaluation_id"] = str(job.latest_evaluation_id)
        return XGBoostChallengerTrainingRequest(
            company_id=job.company_id, material_code=job.material_code, demand_type=job.demand_type,
            training_cutoff_period=job.training_cutoff_period, eligibility_evidence=evidence,
        )

    def _release_resource(self, company_id, job_id, lease_token, reason_code):
        try:
            self._admission_service_factory(self._session_factory, capacity=self._capacity).release(
                company_id, job_id, lease_token, reason_code,
            )
        except RetrainingResourceLeaseError:
            # An expired lease is already recoverable/released by the next
            # admission transaction; terminal runtime state remains immutable.
            pass
