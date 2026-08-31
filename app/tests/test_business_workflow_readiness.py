import unittest
from uuid import uuid4

from app.application.business_workflow_readiness import BusinessWorkflowReadinessService
from app.analysis.backtest import BacktestEngine


class FakeProvider:
    snapshot = {}

    def __init__(self, _session):
        pass

    def preflight(self, _request):
        return self.snapshot


def snapshot(weeks, *, supplier=False):
    return {
        "items": [{"sku_code": "SKU-1", "demand_history": list(range(weeks))}],
        "supplier": {"available": supplier},
    }


class BusinessWorkflowReadinessTests(unittest.TestCase):
    def setUp(self):
        self.service = BusinessWorkflowReadinessService(provider_factory=FakeProvider)

    def evaluate(self, weeks, *, supplier=False):
        FakeProvider.snapshot = snapshot(weeks, supplier=supplier)
        return self.service.evaluate(object(), uuid4(), uuid4(), uuid4())

    def test_twelve_weeks_blocks_only_the_mandatory_backtest_path(self):
        readiness = self.evaluate(12)
        by_capability = {item.capability: item for item in readiness.capabilities}
        self.assertEqual(readiness.status, "BLOCKED")
        self.assertEqual(by_capability["backtest"].reason_code, "INSUFFICIENT_HISTORY")
        self.assertEqual(by_capability["backtest"].required_weeks, 16)
        self.assertEqual(by_capability["backtest"].available_weeks, 12)
        self.assertEqual(by_capability["decision_intelligence"].blocked_by, "backtest")

    def test_backtest_engine_enforces_the_same_default_window_requirement(self):
        result = BacktestEngine().run_backtest(list(range(12)), lead_time_days=7)
        self.assertEqual(result["error"], "Yetersiz veri: En az 16 hafta gerekli")

    def test_sixteen_weeks_is_ready_for_default_backtest_window(self):
        readiness = self.evaluate(16)
        self.assertEqual(readiness.status, "READY")
        self.assertEqual({item.capability: item.status for item in readiness.capabilities}["backtest"], "READY")

    def test_supplier_absence_is_optional_not_a_workflow_blocker(self):
        readiness = self.evaluate(16, supplier=False)
        by_capability = {item.capability: item for item in readiness.capabilities}
        self.assertEqual(readiness.status, "READY")
        self.assertEqual(by_capability["supplier"].status, "OPTIONAL_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
