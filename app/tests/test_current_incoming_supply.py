import unittest
from datetime import date

from app.application.current_incoming_supply import resolve_current_incoming_supply
from app.engine.capability_dataflow import assemble_simulation_business_input
from app.simulation.monte_carlo import MonteCarloInventorySimulator


AS_OF = date(2026, 1, 1)


def supply(rows, *, current=True, horizon=7):
    return resolve_current_incoming_supply(
        {"material_suppliers": rows}, "SKU", current_material_available=current,
        snapshot_as_of=AS_OF, replenishment_horizon_days=horizon,
    )


class CurrentIncomingSupplyTests(unittest.TestCase):
    def test_valid_current_open_order_is_counted_once_in_replenishment_position(self):
        evidence = supply([{"material_code": "SKU", "supplier_code": "A", "open_order": 50, "planned_delivery_date": "2026-01-05"}])
        self.assertEqual(evidence["incoming_supply_qty_used"], 50)
        self.assertEqual(evidence["incoming_supply_status"], "VALID_WITHIN_REPLENISHMENT_HORIZON")
        with_supply = MonteCarloInventorySimulator(n_simulations=1).simulate(50, 7, 1, 0, 0, 10, 100, weeks=3, incoming_supply_schedule=evidence["incoming_supply_schedule"])
        without_supply = MonteCarloInventorySimulator(n_simulations=1).simulate(50, 7, 1, 0, 0, 10, 100, weeks=3)
        self.assertEqual(with_supply["avg_orders"][0], 0)
        self.assertEqual(without_supply["avg_orders"][0], 10)

    def test_omitted_current_snapshot_never_uses_an_old_open_order(self):
        evidence = supply([])
        self.assertEqual(evidence["incoming_supply_qty_used"], 0)
        self.assertEqual(evidence["open_order_snapshot_state"], "CALCULATION_FALLBACK_ZERO")
        self.assertIn("OPEN_ORDER_SNAPSHOT_UNAVAILABLE", evidence["warnings"])

    def test_all_active_absent_sku_never_uses_prior_open_order(self):
        evidence = supply([{"material_code": "SKU", "supplier_code": "A", "open_order": 50, "planned_delivery_date": "2026-01-05"}], current=False)
        self.assertEqual(evidence["incoming_supply_qty_used"], 0)
        self.assertEqual(evidence["incoming_supply_status"], "CURRENT_SNAPSHOT_UNAVAILABLE")

    def test_past_due_and_outside_horizon_deliveries_are_excluded(self):
        past_due = supply([{"material_code": "SKU", "supplier_code": "A", "open_order": 50, "planned_delivery_date": "2025-12-31"}])
        outside = supply([{"material_code": "SKU", "supplier_code": "A", "open_order": 50, "planned_delivery_date": "2026-01-20"}])
        self.assertEqual(past_due["incoming_supply_qty_used"], 0)
        self.assertIn("PAST_DUE_DELIVERY_EXCLUDED", past_due["warnings"])
        self.assertEqual(outside["incoming_supply_qty_used"], 0)
        self.assertIn("DELIVERY_OUTSIDE_REPLENISHMENT_HORIZON", outside["warnings"])

    def test_missing_delivery_date_is_not_fabricated(self):
        evidence = supply([{"material_code": "SKU", "supplier_code": "A", "open_order": 50, "planned_delivery_date": None}])
        self.assertEqual(evidence["incoming_supply_delivery_date"], None)
        self.assertEqual(evidence["incoming_supply_qty_used"], 0)
        self.assertIn("MISSING_PLANNED_DELIVERY", evidence["warnings"])

    def test_multiple_suppliers_sum_once_and_duplicate_supplier_is_excluded(self):
        evidence = supply([
            {"material_code": "SKU", "supplier_code": "A", "open_order": 20, "planned_delivery_date": "2026-01-04"},
            {"material_code": "SKU", "supplier_code": "B", "open_order": 30, "planned_delivery_date": "2026-01-05"},
        ])
        duplicate = supply([
            {"material_code": "SKU", "supplier_code": "A", "open_order": 20, "planned_delivery_date": "2026-01-04"},
            {"material_code": "SKU", "supplier_code": "A", "open_order": 20, "planned_delivery_date": "2026-01-05"},
        ])
        self.assertEqual(evidence["incoming_supply_qty_used"], 50)
        self.assertEqual(duplicate["incoming_supply_qty_used"], 0)
        self.assertIn("DUPLICATE_SUPPLIER_OPEN_ORDER_AMBIGUOUS", duplicate["warnings"])

    def test_explicit_zero_is_distinguished_from_unavailable_snapshot(self):
        evidence = supply([{"material_code": "SKU", "supplier_code": "A", "open_order": 0, "planned_delivery_date": None}])
        self.assertEqual(evidence["open_order_snapshot_state"], "CONFIRMED_ZERO")
        self.assertEqual(evidence["incoming_supply_status"], "CONFIRMED_ZERO")

    def test_validated_supply_snapshot_is_preserved_into_simulation_input_once(self):
        evidence = supply([{"material_code": "SKU", "supplier_code": "A", "open_order": 50, "planned_delivery_date": "2026-01-05"}])
        assembled = assemble_simulation_business_input(
            {"policies": {"SKU": {"initial_stock": 100, "eoq": 80, "incoming_supply": evidence}}},
            {
                "forecast": {"result": {"items": [{"material_code": "SKU", "forecast": [10, 10]}]}, "provenance": {}},
                "safety_stock": {"result": {"items": [{"material_code": "SKU", "safety_stock": 20, "effective_lead_time_used": 7}]}, "provenance": {}},
            },
        )
        self.assertEqual(assembled["items"][0]["incoming_supply"]["incoming_supply_qty_used"], 50)


if __name__ == "__main__":
    unittest.main()
