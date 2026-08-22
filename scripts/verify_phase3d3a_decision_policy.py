"""Focused deterministic/read-only policy contract verification."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from time import perf_counter
from app.application.decision_evidence_resolver import DecisionEvidenceEnvelope
from app.application.decision_policy import DecisionPolicy

def envelope(status="READY", optional=()):
    return DecisionEvidenceEnvelope("company","SKU","sales","2026-W20","REPLENISHMENT",status,
        (("forecast",{"status":"AVAILABLE","source_id":"f"}),("safety_stock",{"status":"AVAILABLE","source_id":"s"})),
        tuple(optional),(),"evidence-fingerprint")
def state(**kwargs): return {"status":"AVAILABLE",**kwargs}
def candidate_types(result): return tuple(c.candidate_type for c in result.candidates)
def main():
    p=DecisionPolicy(); start=perf_counter()
    stable=p.evaluate(envelope(optional=(("company_learning",state(maturity_level="mature")),)))
    assert stable.status=="READY" and candidate_types(stable)==("HOLD_POLICY",)
    insufficient=p.evaluate(envelope("INSUFFICIENT_REQUIRED_EVIDENCE"));assert insufficient.status=="INSUFFICIENT" and not insufficient.candidates
    weak=p.evaluate(envelope(optional=(("backtest",state(signal="weak_validation")),)));assert "REVIEW_FORECAST" in candidate_types(weak) and weak.agreement_status=="CONFLICTED"
    structural=p.evaluate(envelope(optional=(("pattern",state(classification="STRUCTURAL_CHANGE")),)));assert "REVIEW_FORECAST" in candidate_types(structural)
    for classification in ("LATE_PRONE","DETERIORATING","MIXED_RISK"):
        r=p.evaluate(envelope(optional=(("supplier_learning",state(entries=({"classification":classification},))),)));assert "REVIEW_SUPPLIER" in candidate_types(r)
    for classification in ("POSITIVE_ASSOCIATION","NEGATIVE_ASSOCIATION"):
        event=p.evaluate(envelope(optional=(("event",state(entries=({"event_identity":"E","classification":classification},))),)));assert "MONITOR_EVENT_RISK" in candidate_types(event)
    no_clear=p.evaluate(envelope(optional=(("event",state(entries=({"event_identity":"E","classification":"NO_CLEAR_EFFECT"},))),)));assert "MONITOR_EVENT_RISK" not in candidate_types(no_clear)
    for signal in ("stockout_risk","excess_risk"):
        r=p.evaluate(envelope(optional=(("simulation",state(signal=signal)),)));assert "REVIEW_SAFETY_STOCK" in candidate_types(r)
    multi=p.evaluate(envelope(optional=(("pattern",state(classification="VOLATILE")),("supplier_learning",state(entries=({"classification":"LATE_PRONE"},))),("event",state(entries=({"event_identity":"E","classification":"POSITIVE_ASSOCIATION"},))),)));assert candidate_types(multi)==("REVIEW_FORECAST","REVIEW_SUPPLIER","MONITOR_EVENT_RISK")
    low=p.evaluate(envelope(optional=(("company_learning",state(maturity_level="low")),)));assert low.confidence < stable.confidence and candidate_types(low)==("HOLD_POLICY",)
    missing=p.evaluate(envelope());assert missing.status=="READY" and missing.confidence < stable.confidence
    assert p.evaluate(envelope(optional=(("company_learning",state(maturity_level="mature")),)))==stable
    elapsed=(perf_counter()-start)*1000
    print("PHASE 3D3A POLICY PASS",{"policy_ms":round(elapsed,3),"candidate_count":len(multi.candidates),"fingerprint":stable.fingerprint,"writes":0},flush=True)
if __name__=="__main__":main()
