"""Pure semantic closeout for deterministic ``decision_policy_v1``."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.decision_evidence_resolver import DecisionEvidenceEnvelope
from app.application.decision_policy import DecisionPolicy


def envelope(*, status="READY", optional=(), fingerprint="evidence-v1"):
    return DecisionEvidenceEnvelope(
        "company", "SKU", "sales", "2026-W20", "REPLENISHMENT", status,
        (("forecast", {"status": "AVAILABLE", "source_id": "forecast"}),
         ("safety_stock", {"status": "AVAILABLE", "source_id": "safety"})),
        tuple(optional), (), fingerprint,
    )


def available(**values):
    return {"status": "AVAILABLE", **values}


def candidate_types(result):
    return tuple(candidate.candidate_type for candidate in result.candidates)


def main():
    policy = DecisionPolicy()
    stable = policy.evaluate(envelope(optional=(("company_learning", available(maturity_level="mature")),)))
    insufficient = policy.evaluate(envelope(status="INSUFFICIENT_REQUIRED_EVIDENCE"))
    first_use = policy.evaluate(envelope(optional=(("event", {"status": "ABSENT"}),)))
    low_maturity = policy.evaluate(envelope(optional=(("company_learning", available(maturity_level="low")),)))
    assert candidate_types(stable) == ("HOLD_POLICY",) and stable.agreement_status == "ALIGNED"
    assert insufficient.status == "INSUFFICIENT" and insufficient.agreement_status == "INSUFFICIENT" and insufficient.confidence == 0.0
    assert candidate_types(first_use) == ("HOLD_POLICY",) and first_use.confidence < stable.confidence
    assert candidate_types(low_maturity) == candidate_types(stable) and low_maturity.confidence < stable.confidence

    weak_only = policy.evaluate(envelope(optional=(("backtest", available(signal="weak_validation")),)))
    conflict = policy.evaluate(envelope(optional=(
        ("pattern", available(classification="STRUCTURAL_CHANGE")),
        ("backtest", available(signal="weak_validation")),
    )))
    assert candidate_types(weak_only) == ("REVIEW_FORECAST",) and weak_only.agreement_status == "ALIGNED"
    assert candidate_types(conflict) == ("REVIEW_FORECAST",)
    assert conflict.candidates[0].reason_codes == ("BACKTEST_VALIDATION_WEAK", "PATTERN_STRUCTURAL_CHANGE")
    assert conflict.candidates[0].supporting_evidence == ("backtest", "pattern")
    assert conflict.agreement_status == "CONFLICTED"
    assert conflict.conflicting_evidence == ("FORECAST_SIGNAL_VS_WEAK_BACKTEST",)

    duplicate = policy.evaluate(envelope(optional=(
        ("simulation", available(signal="stockout_risk")),
        ("safety_stock", available(signal="excess_risk")),
    )))
    assert candidate_types(duplicate) == ("REVIEW_SAFETY_STOCK",)
    assert duplicate.candidates[0].supporting_evidence == ("safety_stock", "simulation")
    assert duplicate.candidates[0].reason_codes == ("SAFETY_STOCK_REVIEW", "SIMULATION_SCENARIO_RISK")

    supplier = policy.evaluate(envelope(optional=(("supplier_learning", available(entries=(
        {"classification": "VARIABLE"}, {"classification": "LATE_PRONE"},
    ))),)))
    assert candidate_types(supplier) == ("REVIEW_SUPPLIER",)
    assert supplier.candidates[0].reason_codes == ("SUPPLIER_LATE_PRONE", "SUPPLIER_VARIABLE")

    for classification in ("POSITIVE_ASSOCIATION", "NEGATIVE_ASSOCIATION"):
        result = policy.evaluate(envelope(optional=(("event", available(entries=({"classification": classification},))),)))
        assert candidate_types(result) == ("MONITOR_EVENT_RISK",)
    for classification in ("NO_CLEAR_EFFECT", "INCONSISTENT_EFFECT"):
        result = policy.evaluate(envelope(optional=(("event", available(entries=({"classification": classification},))),)))
        assert candidate_types(result) == ("HOLD_POLICY",)

    multi = policy.evaluate(envelope(optional=(
        ("simulation", available(signal="stockout_risk")),
        ("backtest", available(signal="weak_validation")),
        ("supplier_learning", available(entries=({"classification": "LATE_PRONE"},))),
        ("event", available(entries=({"classification": "POSITIVE_ASSOCIATION"},))),
    )))
    assert candidate_types(multi) == ("REVIEW_SAFETY_STOCK", "REVIEW_FORECAST", "REVIEW_SUPPLIER", "MONITOR_EVENT_RISK")
    assert tuple(candidate.priority for candidate in multi.candidates) == (10, 20, 40, 50)
    assert multi.agreement_status == "MIXED" and "HOLD_POLICY" not in candidate_types(multi)

    reordered = policy.evaluate(envelope(optional=tuple(reversed((
        ("event", available(entries=({"classification": "POSITIVE_ASSOCIATION"},))),
        ("supplier_learning", available(entries=({"classification": "LATE_PRONE"},))),
        ("backtest", available(signal="weak_validation")),
        ("simulation", available(signal="stockout_risk")),
    )))))
    assert reordered == multi
    no_event = policy.evaluate(envelope(optional=(
        ("simulation", available(signal="stockout_risk")), ("backtest", available(signal="weak_validation")),
        ("supplier_learning", available(entries=({"classification": "LATE_PRONE"},))),
        ("event", available(entries=({"classification": "NO_CLEAR_EFFECT"},))),
    )))
    assert no_event.fingerprint != multi.fingerprint and candidate_types(no_event) == candidate_types(multi)[:-1]

    print("PHASE 3D3B PURE POLICY PASS", {
        "priority_map": {"simulation": 10, "backtest": 20, "pattern": 30, "retraining": 35, "supplier": 40, "event": 50, "hold": 90},
        "statuses": {"aligned": stable.agreement_status, "mixed": multi.agreement_status, "conflicted": conflict.agreement_status, "insufficient": insufficient.agreement_status},
        "deduplication": "merged candidate reasons and supporting evidence", "writes": 0,
    }, flush=True)


if __name__ == "__main__":
    main()
