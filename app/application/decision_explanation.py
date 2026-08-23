"""Deterministic historical explanation read model for immutable Decision Snapshots."""
from dataclasses import dataclass
from json import dumps, loads
from hashlib import sha256

from app.database import SessionLocal
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate


@dataclass(frozen=True)
class DecisionExplanation:
    snapshot: dict
    decision: dict
    candidates: tuple
    limitations: tuple
    source_provenance: tuple
    explanation_fingerprint: str


class DecisionExplanationService:
    """Reads frozen snapshot evidence only; it never resolves current evidence or calls an LLM."""
    def __init__(self, session_factory=SessionLocal): self._sf = session_factory

    @staticmethod
    def _canonical(value):
        return loads(dumps(value, sort_keys=True, default=str, separators=(",", ":")))

    @staticmethod
    def _source_semantics(name):
        if name == "event": return "NON_CAUSAL_ASSOCIATION"
        if name == "simulation": return "SCENARIO_EVIDENCE"
        if name == "backtest": return "VALIDATION_EVIDENCE"
        if name in {"pattern", "supplier_learning", "company_learning", "retraining"}: return "LEARNED_CONTEXT"
        return "FACT_AUTHORITATIVE_INPUT"

    def get(self, company_id, decision_snapshot_id):
        session = self._sf()
        try:
            snapshot = session.query(DecisionSnapshot).filter_by(id=decision_snapshot_id, company_id=company_id).one_or_none()
            if snapshot is None: return None
            candidates = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id).order_by(DecisionSnapshotCandidate.ordinal).all()
            provenance = snapshot.source_provenance or {}
            sources = []
            for group in ("required", "optional", "hints"):
                entries = provenance.get(group, [])
                if isinstance(entries, dict): entries = entries.items()
                for name, value in entries:
                    sources.append({"group": group, "source": name, "semantic_type": self._source_semantics(name), "evidence": self._canonical(value)})
            sources = tuple(sorted(sources, key=lambda row: (row["group"], row["source"])))
            result = DecisionExplanation(
                snapshot={"id": str(snapshot.id), "company_id": str(snapshot.company_id), "material_code": snapshot.material_code,
                    "demand_type": snapshot.demand_type, "decision_context": snapshot.decision_context,
                    "cutoff": snapshot.decision_cutoff_period, "generated_at": snapshot.generated_at.isoformat()},
                decision={"status": snapshot.status, "agreement_status": snapshot.agreement_status, "confidence": float(snapshot.confidence),
                    "confidence_policy_version": snapshot.confidence_policy_version, "confidence_semantics": "evidence quality, completeness, and maturity; not success probability, forecast accuracy, causal certainty, or business outcome probability",
                    "policy_version": snapshot.decision_policy_version, "policy_fingerprint": snapshot.decision_policy_fingerprint,
                    "supporting_evidence": tuple(snapshot.supporting_evidence or ()), "conflicting_evidence": tuple(snapshot.conflicting_evidence or ()),
                    "uncertainty_codes": tuple(snapshot.uncertainty_codes or ())},
                candidates=tuple({"ordinal": row.ordinal, "candidate_type": row.candidate_type, "severity": row.severity, "priority": row.priority,
                    "reason_codes": tuple(row.reason_codes or ()), "supporting_evidence": tuple(row.supporting_evidence or ()),
                    "conflicting_evidence": tuple(row.conflicting_evidence or ()), "confidence": float(row.confidence),
                    "expected_impact_references": tuple(row.expected_impact_references or ()), "what_would_change_this": tuple(row.what_would_change_this or ())} for row in candidates),
                limitations=tuple(sorted(snapshot.uncertainty_codes or ())), source_provenance=sources, explanation_fingerprint="")
            fingerprint = sha256(dumps({"snapshot": result.snapshot, "decision": result.decision, "candidates": result.candidates,
                "limitations": result.limitations, "source_provenance": result.source_provenance}, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
            return DecisionExplanation(result.snapshot, result.decision, result.candidates, result.limitations, result.source_provenance, fingerprint)
        finally: session.close()
