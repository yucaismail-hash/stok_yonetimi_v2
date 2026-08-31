import unittest
from types import SimpleNamespace
from uuid import uuid4

from app.analysis.backtest import BacktestEngine
from app.application.business_workflow_readiness import BusinessWorkflowReadinessService
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider


class FakeProvider:
    snapshot = {}

    def __init__(self, _session):
        pass

    def preflight(self, _request):
        return self.snapshot


def item(code, weeks, *, product_name=None, current_snapshot=True, scope_source="LATEST_UPLOAD"):
    return {
        "sku_code": code,
        "product_name": product_name or code,
        "demand_history": list(range(weeks)),
        "history_periods": [f"2026-W{index:02d}" for index in range(1, weeks + 1)],
        "current_snapshot_available": current_snapshot,
        "scope_source": scope_source,
        "temporal_warnings": [] if current_snapshot else ["CURRENT_SNAPSHOT_UNAVAILABLE"],
    }


def snapshot(*items, supplier=False):
    latest = sum(row["scope_source"] == "LATEST_UPLOAD" for row in items)
    absent = len(items) - latest
    stale = sum("EFFECTIVE_MASTER_FROM_PRIOR_UPLOAD" in row["temporal_warnings"] for row in items)
    return {"items": list(items), "supplier": {"available": supplier}, "scope": {"scope_mode": "ALL_ACTIVE_SKUS" if absent else "LATEST_UPLOAD", "latest_upload_count": latest, "absent_from_latest_upload_count": absent, "current_snapshot_warning_count": absent, "stale_master_warning_count": stale}}


class BusinessWorkflowReadinessTests(unittest.TestCase):
    def setUp(self):
        self.service = BusinessWorkflowReadinessService(provider_factory=FakeProvider)

    def evaluate(self, *items, supplier=False):
        FakeProvider.snapshot = snapshot(*items, supplier=supplier)
        return self.service.evaluate(object(), uuid4(), uuid4(), uuid4())

    def test_backtest_engine_enforces_the_same_default_window_requirement(self):
        result = BacktestEngine().run_backtest(list(range(12)), lead_time_days=7)
        self.assertEqual(result["error"], "Yetersiz veri: En az 16 hafta gerekli")

    def test_effective_persisted_history_of_52_plus_new_week_is_53_not_latest_upload_one(self):
        # The provider contract is the effective persisted period set, not upload rows.
        readiness = self.evaluate(item("SKU-1", 53))
        material = readiness.materials[0]
        self.assertEqual(material.available_weeks, 53)
        self.assertEqual(material.latest_observation_period, "2026-W53")
        self.assertEqual(readiness.status, "READY")
        self.assertEqual(readiness.eligible_material_codes("backtest"), ("SKU-1",))

    def test_effective_correction_replaces_a_period_without_double_counting(self):
        # A correction changes one effective value but preserves the 52 + 1 period count.
        readiness = self.evaluate(item("SKU-1", 53))
        self.assertEqual(readiness.materials[0].available_weeks, 53)
        self.assertEqual(readiness.coverage.fully_analyzed_count, 1)

    def test_mixed_history_is_ready_with_backtest_exclusion_not_globally_blocked(self):
        readiness = self.evaluate(item("SKU-A", 53), item("SKU-B", 38), item("SKU-C", 7, product_name="Kısa Geçmiş"))
        self.assertEqual(readiness.status, "READY_WITH_EXCLUSIONS")
        self.assertEqual(readiness.eligible_material_codes("backtest"), ("SKU-A", "SKU-B"))
        self.assertEqual(readiness.eligible_material_codes("decision_intelligence"), ("SKU-A", "SKU-B"))
        self.assertEqual(readiness.coverage.total_scope_count, 3)
        self.assertEqual(readiness.coverage.fully_analyzed_count, 2)
        self.assertEqual(readiness.coverage.partially_analyzed_count, 1)
        self.assertEqual(readiness.coverage.excluded_count, 0)
        exclusion = next(item for item in readiness.coverage.exclusions if item.material_code == "SKU-C" and item.capability == "backtest")
        self.assertEqual((exclusion.status, exclusion.reason_code, exclusion.available_weeks, exclusion.required_weeks), ("EXCLUDED", "INSUFFICIENT_HISTORY", 7, 16))
        sku_c = next(material for material in readiness.materials if material.material_code == "SKU-C")
        self.assertEqual({row.capability: row.status for row in sku_c.capabilities}["forecast"], "READY")
        self.assertEqual({row.capability: row.status for row in sku_c.capabilities}["backtest"], "EXCLUDED")

    def test_all_active_includes_absent_sku_with_persisted_history_but_no_current_snapshot(self):
        readiness = self.evaluate(item("LATEST", 53), item("HISTORICAL", 38, current_snapshot=False, scope_source="ALL_ACTIVE_SKUS"))
        historical = next(row for row in readiness.materials if row.material_code == "HISTORICAL")
        status = {row.capability: row.status for row in historical.capabilities}
        self.assertEqual(readiness.coverage.scope_mode, "ALL_ACTIVE_SKUS")
        self.assertEqual(readiness.coverage.latest_upload_count, 1)
        self.assertEqual(readiness.coverage.absent_from_latest_upload_count, 1)
        self.assertEqual(historical.available_weeks, 38)
        self.assertEqual(status["backtest"], "READY")
        self.assertEqual(status["simulation"], "EXCLUDED")
        self.assertEqual(status["decision_intelligence"], "EXCLUDED")
        self.assertEqual(readiness.eligible_material_codes("simulation"), ("LATEST",))

    def test_blank_optional_master_value_preserves_prior_accepted_value_without_snapshot_carry_forward(self):
        current = SimpleNamespace(
            lead_time_days=7, lot_size=10, unit_cost=None, holding_rate=None, stockout_cost=None,
            product_level="finished_good", product_group="A", product_class="X", initial_stock=25,
        )
        previous = SimpleNamespace(
            lead_time_days=5, lot_size=8, unit_cost=12.5, holding_rate=0.2, stockout_cost=33,
            product_level="finished_good", product_group="A", product_class="X", initial_stock=999,
        )
        master, inherited = DatasetRuntimeProvider._effective_master_values(current, [current, previous])
        self.assertTrue(inherited)
        self.assertEqual(master["lead_time_days"], 7)
        self.assertEqual(master["lot_size"], 10)
        self.assertEqual(master["unit_cost"], 12.5)
        self.assertEqual(master["holding_rate"], 0.2)
        self.assertEqual(master["stockout_cost"], 33)
        self.assertNotIn("initial_stock", master)

    def test_all_materials_below_mandatory_backtest_threshold_is_blocked(self):
        readiness = self.evaluate(item("SKU-A", 12), item("SKU-B", 7))
        self.assertEqual(readiness.status, "BLOCKED")
        self.assertFalse(readiness.is_ready)
        self.assertEqual(readiness.eligible_material_codes("backtest"), ())

    def test_supplier_absence_is_optional_not_a_workflow_blocker(self):
        readiness = self.evaluate(item("SKU-1", 16), supplier=False)
        by_capability = {item.capability: item for item in readiness.capabilities}
        self.assertEqual(readiness.status, "READY")
        self.assertEqual(by_capability["supplier"].status, "OPTIONAL_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
