"""Materializes immutable audit vintages from canonical Decision outputs only."""
from dataclasses import dataclass
from json import dumps, loads
from time import perf_counter
from sqlalchemy.exc import IntegrityError

from app.application.decision_evidence_resolver import DecisionEvidenceEnvelope
from app.application.decision_policy import DecisionPolicy, DecisionPolicyResult
from app.database import SessionLocal
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate


@dataclass(frozen=True)
class DecisionSnapshotMaterialization:
    status: str
    snapshot_id: object
    elapsed_ms: float


class DecisionSnapshotService:
    """Writes only immutable snapshot rows; Resolver remains the cutoff authority."""
    def __init__(self, session_factory=SessionLocal): self._sf = session_factory

    @staticmethod
    def _canonical(value):
        return loads(dumps(value, sort_keys=True, default=str, separators=(",", ":")))

    def materialize(self, envelope, policy_result):
        if not isinstance(envelope, DecisionEvidenceEnvelope) or not isinstance(policy_result, DecisionPolicyResult):
            raise ValueError("materialize requires canonical DecisionEvidenceEnvelope and DecisionPolicyResult")
        if DecisionPolicy().evaluate(envelope) != policy_result:
            raise ValueError("policy result is not derived from supplied envelope")
        started = perf_counter(); session = self._sf()
        try:
            identity = dict(company_id=envelope.company_id, material_code=envelope.material_code, demand_type=envelope.demand_type,
                decision_context=envelope.decision_context, decision_cutoff_period=envelope.decision_cutoff_period,
                decision_policy_version=policy_result.policy_version, decision_evidence_fingerprint=envelope.fingerprint,
                decision_policy_fingerprint=policy_result.fingerprint)
            existing = session.query(DecisionSnapshot).filter_by(**identity).one_or_none()
            if existing:
                return DecisionSnapshotMaterialization("ALREADY_EXISTS", existing.id, (perf_counter()-started)*1000)
            snapshot = DecisionSnapshot(**identity, confidence_policy_version=policy_result.confidence_policy_version,
                status=policy_result.status, agreement_status=policy_result.agreement_status, confidence=policy_result.confidence,
                supporting_evidence=self._canonical(policy_result.supporting_evidence), conflicting_evidence=self._canonical(policy_result.conflicting_evidence),
                uncertainty_codes=self._canonical(policy_result.uncertainty_codes),
                source_provenance=self._canonical({"required": envelope.required, "optional": envelope.optional, "hints": envelope.hints}))
            session.add(snapshot); session.flush()
            for ordinal, candidate in enumerate(policy_result.candidates, 1):
                session.add(DecisionSnapshotCandidate(decision_snapshot_id=snapshot.id, ordinal=ordinal,
                    candidate_type=candidate.candidate_type, severity=candidate.severity, priority=candidate.priority,
                    reason_codes=self._canonical(candidate.reason_codes), supporting_evidence=self._canonical(candidate.supporting_evidence),
                    conflicting_evidence=self._canonical(candidate.conflicting_evidence), confidence=candidate.confidence,
                    expected_impact_references=self._canonical(candidate.expected_impact_references), what_would_change_this=self._canonical(candidate.what_would_change_this)))
            session.commit()
            return DecisionSnapshotMaterialization("CREATED", snapshot.id, (perf_counter()-started)*1000)
        except IntegrityError:
            session.rollback()
            existing = session.query(DecisionSnapshot).filter_by(**identity).one()
            return DecisionSnapshotMaterialization("ALREADY_EXISTS", existing.id, (perf_counter()-started)*1000)
        finally: session.close()

    def get(self, company_id, snapshot_id):
        session=self._sf()
        try:return session.query(DecisionSnapshot).filter_by(id=snapshot_id, company_id=company_id).one_or_none()
        finally: session.close()

    def list_for_scope(self, company_id, material_code, demand_type, decision_context):
        session=self._sf()
        try:return tuple(session.query(DecisionSnapshot).filter_by(company_id=company_id, material_code=material_code, demand_type=demand_type, decision_context=decision_context).order_by(DecisionSnapshot.generated_at, DecisionSnapshot.id).all())
        finally: session.close()
