"""Single-concurrency durable Business Workflow worker entrypoint."""

import asyncio
import logging
import os
import signal
import socket
from dataclasses import dataclass

from app.database import SessionLocal
from app.config.production_safety import validate_worker_production_configuration
from app.engine.business_workflow_scheduler import BusinessWorkflowScheduler
from app.engine.local_forecast_runner import LocalForecastRunner
from app.engine.runtime_store import RuntimeStoreConcurrencyError
from app.models.runtime import RuntimeExecution


logger = logging.getLogger(__name__)
ACTIVE_STATES = ("created", "queued", "running", "waiting", "retrying")


@dataclass(frozen=True)
class WorkerSettings:
    poll_seconds: float = 5.0
    lease_seconds: int = 900
    worker_id: str = "business-workflow-worker"

    @classmethod
    def from_env(cls):
        validate_worker_production_configuration()
        poll_seconds = float(os.getenv("BUSINESS_WORKFLOW_POLL_SECONDS", "5"))
        lease_seconds = int(os.getenv("BUSINESS_WORKFLOW_LEASE_SECONDS", "900"))
        worker_id = os.getenv("BUSINESS_WORKFLOW_WORKER_ID") or f"business-workflow-{socket.gethostname()}-{os.getpid()}"
        if poll_seconds < 1 or poll_seconds > 60:
            raise ValueError("BUSINESS_WORKFLOW_POLL_SECONDS must be between 1 and 60")
        if lease_seconds < 600 or lease_seconds > 3600:
            raise ValueError("BUSINESS_WORKFLOW_LEASE_SECONDS must be between 600 and 3600")
        return cls(poll_seconds, lease_seconds, worker_id)


class BusinessWorkflowWorker:
    """Poll durable executions and run at most one task at a time."""

    def __init__(self, settings=None, session_factory=SessionLocal, scheduler_factory=BusinessWorkflowScheduler):
        self.settings = settings or WorkerSettings.from_env()
        self._session_factory = session_factory
        self._scheduler_factory = scheduler_factory

    def _runner(self):
        return LocalForecastRunner(
            session_factory=self._session_factory,
            worker_id=self.settings.worker_id,
            lease_seconds=self.settings.lease_seconds,
        )

    async def process_next(self) -> bool:
        session = self._session_factory()
        try:
            candidates = (
                session.query(RuntimeExecution.execution_id, RuntimeExecution.company_id)
                .filter(
                    RuntimeExecution.analysis_type == "business_workflow",
                    RuntimeExecution.state.in_(ACTIVE_STATES),
                )
                .order_by(RuntimeExecution.created_at.asc())
                .limit(25)
                .all()
            )
            for execution_id, company_id in candidates:
                scheduler = self._scheduler_factory(session, runner_factory=self._runner)
                try:
                    result = await scheduler.run_next_ready(execution_id, company_id)
                except RuntimeStoreConcurrencyError:
                    session.rollback()
                    logger.info("workflow_task_claim_lost", extra={"execution_id": str(execution_id)})
                    continue
                if result is not None:
                    logger.info("workflow_task_processed", extra={"execution_id": str(execution_id)})
                    return True
            return False
        finally:
            session.close()

    async def run(self, stop_event: asyncio.Event):
        logger.info(
            "business_workflow_worker_started",
            extra={"worker_id": self.settings.worker_id, "poll_seconds": self.settings.poll_seconds},
        )
        while not stop_event.is_set():
            try:
                worked = await self.process_next()
            except Exception as exc:
                logger.error(
                    "business_workflow_worker_iteration_failed",
                    extra={"error_code": type(exc).__name__},
                )
                worked = False
            if not worked:
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=self.settings.poll_seconds)
                except asyncio.TimeoutError:
                    pass
        logger.info("business_workflow_worker_stopped", extra={"worker_id": self.settings.worker_id})


async def _main():
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, stop_event.set)
        except NotImplementedError:
            signal.signal(signum, lambda *_: loop.call_soon_threadsafe(stop_event.set))
    await BusinessWorkflowWorker().run(stop_event)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    asyncio.run(_main())
