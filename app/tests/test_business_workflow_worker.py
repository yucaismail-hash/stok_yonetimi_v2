import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from app.workers.business_workflow import BusinessWorkflowWorker, WorkerSettings


class FakeQuery:
    def __init__(self, candidates):
        self.candidates = candidates

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def limit(self, value):
        return self

    def all(self):
        return self.candidates


class FakeSession:
    def __init__(self, candidates):
        self.candidates = candidates
        self.closed = False
        self.rolled_back = False

    def query(self, *args):
        return FakeQuery(self.candidates)

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeScheduler:
    calls = []
    result = None

    def __init__(self, session, runner_factory):
        self.session = session
        self.runner_factory = runner_factory

    async def run_next_ready(self, execution_id, company_id):
        self.calls.append((execution_id, company_id))
        return self.result


class BusinessWorkflowWorkerTests(unittest.TestCase):
    def setUp(self):
        FakeScheduler.calls = []
        FakeScheduler.result = None

    def test_settings_have_bounded_single_worker_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = WorkerSettings.from_env()
        self.assertEqual(settings.poll_seconds, 5)
        self.assertEqual(settings.lease_seconds, 900)
        self.assertTrue(settings.worker_id.startswith("business-workflow-"))

    def test_invalid_lease_is_rejected(self):
        with patch.dict(os.environ, {"BUSINESS_WORKFLOW_LEASE_SECONDS": "30"}, clear=True):
            with self.assertRaises(ValueError):
                WorkerSettings.from_env()

    def test_process_next_returns_false_without_durable_candidates(self):
        session = FakeSession([])
        worker = BusinessWorkflowWorker(
            WorkerSettings(worker_id="test-worker"),
            session_factory=lambda: session,
            scheduler_factory=FakeScheduler,
        )
        self.assertFalse(asyncio.run(worker.process_next()))
        self.assertTrue(session.closed)

    def test_process_next_delegates_one_durable_execution(self):
        execution_id, company_id = uuid4(), uuid4()
        session = FakeSession([(execution_id, company_id)])
        FakeScheduler.result = SimpleNamespace(id=uuid4())
        worker = BusinessWorkflowWorker(
            WorkerSettings(worker_id="test-worker"),
            session_factory=lambda: session,
            scheduler_factory=FakeScheduler,
        )
        self.assertTrue(asyncio.run(worker.process_next()))
        self.assertEqual(FakeScheduler.calls, [(execution_id, company_id)])
        self.assertTrue(session.closed)

    def test_pre_signalled_shutdown_does_not_poll(self):
        stop = asyncio.Event()
        stop.set()
        worker = BusinessWorkflowWorker(
            WorkerSettings(worker_id="test-worker"),
            session_factory=lambda: FakeSession([]),
            scheduler_factory=FakeScheduler,
        )
        asyncio.run(worker.run(stop))
        self.assertEqual(FakeScheduler.calls, [])


if __name__ == "__main__":
    unittest.main()
