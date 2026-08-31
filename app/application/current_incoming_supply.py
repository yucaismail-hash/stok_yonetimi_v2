"""Current-upload incoming-supply normalization for Business Workflow simulation.

This module is intentionally pure.  It never reads historical supplier rows:
open orders and planned delivery dates are operational snapshots, not master
data.  The Official V3 sheet has no purchase-order identity, so one row is an
aggregate snapshot for one material/supplier pair.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from math import ceil
from typing import Any


def _as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _quantity(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if value >= 0 else None


def resolve_current_incoming_supply(
    supplier_inputs: Any,
    material_code: str,
    *,
    current_material_available: bool,
    snapshot_as_of: date,
    replenishment_horizon_days: float,
) -> dict[str, Any]:
    """Return only valid, current-snapshot incoming supply for one material.

    A planned delivery must be strictly future and arrive within the current
    replenishment horizon.  Missing and ambiguous snapshot values fall back to
    zero for calculation, while metadata preserves that this is not a confirmed
    zero.
    """
    base = {
        "incoming_supply_qty_used": 0.0,
        "incoming_supply_delivery_date": None,
        "incoming_supply_delivery_dates": [],
        "incoming_supply_schedule": [],
        "open_order_snapshot_state": "CALCULATION_FALLBACK_ZERO",
        "incoming_supply_status": "OPEN_ORDER_SNAPSHOT_UNAVAILABLE",
        "warnings": [],
    }
    if not current_material_available:
        return {
            **base,
            "incoming_supply_status": "CURRENT_SNAPSHOT_UNAVAILABLE",
            "warnings": ["CURRENT_SNAPSHOT_UNAVAILABLE"],
        }
    mappings = supplier_inputs.get("material_suppliers") if isinstance(supplier_inputs, dict) else None
    if not isinstance(mappings, list):
        return {**base, "warnings": ["OPEN_ORDER_SNAPSHOT_UNAVAILABLE"]}
    rows = [
        row for row in mappings
        if isinstance(row, dict) and row.get("material_code") == material_code
    ]
    if not rows:
        return {**base, "warnings": ["OPEN_ORDER_SNAPSHOT_UNAVAILABLE"]}

    by_supplier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        supplier = row.get("supplier_code")
        if isinstance(supplier, str) and supplier.strip():
            by_supplier[supplier].append(row)

    horizon_days = max(1, int(ceil(replenishment_horizon_days)))
    valid, statuses, warnings, explicit_quantities = [], [], [], []
    for supplier, supplier_rows in sorted(by_supplier.items()):
        # No PO identity exists in V3.  Two rows for the same pair are
        # ambiguous aggregate snapshots, never two safely addable orders.
        if len(supplier_rows) != 1:
            statuses.append("DUPLICATE_SUPPLIER_OPEN_ORDER_AMBIGUOUS")
            warnings.append("DUPLICATE_SUPPLIER_OPEN_ORDER_AMBIGUOUS")
            continue
        row = supplier_rows[0]
        quantity = _quantity(row.get("open_order"))
        if quantity is None:
            statuses.append("OPEN_ORDER_NOT_SUPPLIED")
            warnings.append("OPEN_ORDER_NOT_SUPPLIED")
            continue
        explicit_quantities.append(quantity)
        if quantity == 0:
            statuses.append("CONFIRMED_ZERO")
            continue
        planned = _as_date(row.get("planned_delivery_date"))
        if planned is None:
            statuses.append("MISSING_PLANNED_DELIVERY")
            warnings.append("MISSING_PLANNED_DELIVERY")
            continue
        days_until = (planned - snapshot_as_of).days
        if days_until <= 0:
            statuses.append("PAST_DUE_DELIVERY_EXCLUDED")
            warnings.append("PAST_DUE_DELIVERY_EXCLUDED")
            continue
        if days_until > horizon_days:
            statuses.append("DELIVERY_OUTSIDE_REPLENISHMENT_HORIZON")
            warnings.append("DELIVERY_OUTSIDE_REPLENISHMENT_HORIZON")
            continue
        valid.append({
            "supplier_code": supplier,
            "quantity": quantity,
            "planned_delivery_date": planned.isoformat(),
            "arrival_week": int(ceil(days_until / 7)),
        })
        statuses.append("VALID_WITHIN_REPLENISHMENT_HORIZON")

    if valid:
        dates = sorted({row["planned_delivery_date"] for row in valid})
        return {
            "incoming_supply_qty_used": sum(row["quantity"] for row in valid),
            "incoming_supply_delivery_date": dates[0],
            "incoming_supply_delivery_dates": dates,
            "incoming_supply_schedule": [
                {"quantity": row["quantity"], "arrival_week": row["arrival_week"]}
                for row in valid
            ],
            "open_order_snapshot_state": "SNAPSHOT_SUPPLIED",
            "incoming_supply_status": "VALID_WITHIN_REPLENISHMENT_HORIZON",
            "warnings": sorted(set(warnings)),
        }
    if explicit_quantities and all(quantity == 0 for quantity in explicit_quantities) and not warnings:
        return {**base, "open_order_snapshot_state": "CONFIRMED_ZERO", "incoming_supply_status": "CONFIRMED_ZERO"}
    return {
        **base,
        "open_order_snapshot_state": "SNAPSHOT_SUPPLIED" if explicit_quantities else "CALCULATION_FALLBACK_ZERO",
        "incoming_supply_status": "NO_VALID_INCOMING_SUPPLY",
        "warnings": sorted(set(warnings or statuses)),
    }
