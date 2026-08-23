"""Pure, deterministic candidate policy over canonical Decision Evidence."""
from dataclasses import dataclass
from hashlib import sha256
from json import dumps

POLICY_VERSION = "decision_policy_v1"
CONFIDENCE_VERSION = "decision_confidence_v1"

@dataclass(frozen=True)
class DecisionCandidate:
    candidate_type: str; severity: str; priority: int; decision_context: str
    reason_codes: tuple; supporting_evidence: tuple; conflicting_evidence: tuple
    confidence: float; expected_impact_references: tuple; what_would_change_this: tuple

@dataclass(frozen=True)
class DecisionPolicyResult:
    policy_version: str; confidence_policy_version: str; status: str; agreement_status: str
    candidates: tuple; supporting_evidence: tuple; conflicting_evidence: tuple
    uncertainty_codes: tuple; confidence: float; fingerprint: str

class DecisionPolicy:
    """No database access, persistence, model execution, or autonomous action."""
    _ORDER = {"REVIEW_SAFETY_STOCK": 0, "REVIEW_REORDER_POLICY": 1, "REVIEW_FORECAST": 2,
              "REVIEW_SUPPLIER": 3, "MONITOR_EVENT_RISK": 4, "HOLD_POLICY": 5, "NO_ACTION": 6}
    _SUPPLIER_RISKS = {"LATE_PRONE", "VARIABLE", "FULFILLMENT_RISK", "DETERIORATING", "MIXED_RISK"}
    _PATTERN_RISKS = {"STRUCTURAL_CHANGE", "VOLATILE", "INTERMITTENT", "LUMPY"}
    _SEVERITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    def evaluate(self, envelope):
        required=dict(envelope.required); optional=dict(envelope.optional)
        uncertainty=tuple(sorted(name+"_"+value.get("status", "ABSENT") for name,value in optional.items() if value.get("status") != "AVAILABLE"))
        if envelope.status != "READY":
            return self._result(envelope,"INSUFFICIENT","INSUFFICIENT",(),(),(),("REQUIRED_EVIDENCE_INSUFFICIENT",),0.0)
        support=[]; conflicts=[]; candidates={}; forecast_review_context=False
        def add(kind,severity,priority,reason,evidence,change):
            """Merge same-kind recommendations without dropping source provenance."""
            current=candidates.get(kind)
            if current is None:
                candidates[kind]={"severity":severity,"priority":priority,"reasons":{reason},"evidence":set(evidence),"changes":{change}}
                return
            current["severity"]=severity if self._SEVERITY_RANK[severity]>self._SEVERITY_RANK[current["severity"]] else current["severity"]
            current["priority"]=min(current["priority"],priority)
            current["reasons"].add(reason);current["evidence"].update(evidence);current["changes"].add(change)
        pattern=optional.get("pattern",{}); classification=pattern.get("classification")
        if classification in self._PATTERN_RISKS:
            add("REVIEW_FORECAST","MEDIUM",30,"PATTERN_"+classification,("pattern",),"compatible pattern becomes stable")
            support.append("PATTERN_"+classification)
            forecast_review_context=True
        supplier=optional.get("supplier_learning",{}); supplier_classes=tuple(sorted({x.get("classification") for x in supplier.get("entries",()) if x.get("classification")}))
        risks=tuple(x for x in supplier_classes if x in self._SUPPLIER_RISKS)
        if risks:
            for risk in risks:add("REVIEW_SUPPLIER","MEDIUM",40,"SUPPLIER_"+risk,("supplier_learning",),"supplier risk evidence improves")
            support.extend("SUPPLIER_"+x for x in risks)
        events=optional.get("event",{}).get("entries",())
        actionable_events=tuple(event for event in events if event.get("classification") in {"POSITIVE_ASSOCIATION","NEGATIVE_ASSOCIATION"})
        if actionable_events:
            add("MONITOR_EVENT_RISK","LOW",50,"EVENT_ASSOCIATION",("event",),"event association evidence changes")
            support.append("EVENT_ASSOCIATION_NON_CAUSAL")
        retraining=optional.get("retraining",{})
        if retraining.get("status")=="AVAILABLE" and retraining.get("state") in {"pending","queued","running","trained"}:
            add("REVIEW_FORECAST","MEDIUM",35,"RETRAINING_CONTEXT",("retraining",),"retraining context settles")
            support.append("RETRAINING_CONTEXT")
            forecast_review_context=True
        # Runtime envelopes intentionally expose provenance, not unverified numerical semantics.
        # A compact explicit risk signal may be supplied by a future resolver contract.
        for key,kind,reason in (("simulation","REVIEW_SAFETY_STOCK","SIMULATION_SCENARIO_RISK"),("safety_stock","REVIEW_SAFETY_STOCK","SAFETY_STOCK_REVIEW"),("backtest","REVIEW_FORECAST","BACKTEST_VALIDATION_WEAK")):
            value=optional.get(key, required.get(key,{}))
            if value.get("signal") in {"stockout_risk","excess_risk","weak_validation"}:
                add(kind,"HIGH" if key=="simulation" else "MEDIUM",10 if key=="simulation" else 20,reason,(key,),"compatible validation/scenario evidence improves")
                support.append(reason)
        if forecast_review_context and optional.get("backtest",{}).get("signal")=="weak_validation":
            conflicts.append("FORECAST_SIGNAL_VS_WEAK_BACKTEST")
        if not candidates:
            add("HOLD_POLICY","LOW",90,"STABLE_VALIDATED_EVIDENCE",("forecast",),"compatible risk evidence appears")
            support.append("STABLE_VALIDATED_EVIDENCE")
        coverage=sum(1 for value in optional.values() if value.get("status")=="AVAILABLE")/max(len(optional),1)
        maturity=optional.get("company_learning",{}).get("maturity_level")
        maturity_weight={"mature":1.0,"developing":.85,"low":.7}.get(str(maturity).lower(),.8)
        confidence=round((.6+.4*coverage)*maturity_weight,3)
        candidates=[DecisionCandidate(kind,data["severity"],data["priority"],envelope.decision_context,tuple(sorted(data["reasons"])),tuple(sorted(data["evidence"])),(),confidence,(),tuple(sorted(data["changes"]))) for kind,data in candidates.items()]
        candidates=tuple(sorted(candidates,key=lambda c:(c.priority,self._ORDER[c.candidate_type],c.candidate_type,c.reason_codes)))
        agreement="CONFLICTED" if conflicts else ("MIXED" if len(candidates)>1 else "ALIGNED")
        return self._result(envelope,"READY",agreement,candidates,tuple(sorted(set(support))),tuple(sorted(set(conflicts))),uncertainty,confidence)
    def _result(self,envelope,status,agreement,candidates,support,conflicts,uncertainty,confidence):
        semantic={"envelope":envelope.fingerprint,"policy":POLICY_VERSION,"confidence":CONFIDENCE_VERSION,"status":status,"agreement":agreement,"candidates":candidates,"support":support,"conflicts":conflicts,"uncertainty":uncertainty,"score":confidence}
        fp=sha256(dumps(semantic,sort_keys=True,default=str,separators=(",",":" )).encode()).hexdigest()
        return DecisionPolicyResult(POLICY_VERSION,CONFIDENCE_VERSION,status,agreement,tuple(candidates),tuple(support),tuple(conflicts),tuple(uncertainty),confidence,fp)
