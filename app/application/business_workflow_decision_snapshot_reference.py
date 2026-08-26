"""Immutable provenance persistence and read boundary for workflow Decisions."""

from dataclasses import dataclass
from time import perf_counter

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.business_workflow_decision_finalization import BusinessWorkflowDecisionFinalization
from app.models.business_workflow_decision_snapshot_reference import BusinessWorkflowDecisionSnapshotReference
from app.models.decision_snapshot import DecisionSnapshot


class DecisionSnapshotReferenceError(ValueError):
    pass


@dataclass(frozen=True)
class DecisionSnapshotReference:
    id: object
    company_id: object
    execution_id: object
    decision_finalization_id: object
    decision_snapshot_id: object
    material_code: str
    demand_type: str
    decision_context: str
    decision_cutoff_period: str


class BusinessWorkflowDecisionSnapshotReferenceService:
    """Never resolves or materializes Decisions; it writes/reads exact provenance."""

    def __init__(self, session_factory=SessionLocal):
        self._sf = session_factory

    @staticmethod
    def _view(row):
        return DecisionSnapshotReference(
            row.id, row.company_id, row.execution_id, row.decision_finalization_id,
            row.decision_snapshot_id, row.material_code, row.demand_type,
            row.decision_context, row.decision_cutoff_period,
        )

    def ensure_for_plan(self, company_id, execution_id, decision_finalization_id, plan):
        """Persist one idempotent association per successfully materialized scope."""
        started = perf_counter()
        references = []
        for item in plan.items:
            snapshot_id = item.get("decision_snapshot_id") if isinstance(item, dict) else None
            material_code = item.get("material_code") if isinstance(item, dict) else None
            if not snapshot_id or not material_code:
                raise DecisionSnapshotReferenceError("Decision plan item lacks snapshot provenance")
            references.append(self._ensure_one(
                company_id, execution_id, decision_finalization_id, snapshot_id, material_code,
                plan.demand_type, plan.decision_context, plan.decision_cutoff_period,
            ))
        return tuple(references), (perf_counter() - started) * 1000

    def _ensure_one(self, company_id, execution_id, decision_finalization_id, snapshot_id, material_code, demand_type, context, cutoff):
        session = self._sf()
        try:
            finalization = session.query(BusinessWorkflowDecisionFinalization).filter_by(
                id=decision_finalization_id, company_id=company_id, execution_id=execution_id
            ).one_or_none()
            snapshot = session.query(DecisionSnapshot).filter_by(id=snapshot_id, company_id=company_id).one_or_none()
            if finalization is None or snapshot is None:
                raise DecisionSnapshotReferenceError("company-scoped finalization or Snapshot is unavailable")
            expected = (material_code, demand_type, context, cutoff)
            actual = (snapshot.material_code, snapshot.demand_type, snapshot.decision_context, snapshot.decision_cutoff_period)
            if actual != expected:
                raise DecisionSnapshotReferenceError("Snapshot provenance does not match completed workflow Decision scope")
            existing = session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(
                company_id=company_id, execution_id=execution_id, material_code=material_code,
                demand_type=demand_type, decision_context=context,
            ).one_or_none()
            if existing is not None:
                if existing.decision_snapshot_id != snapshot.id or existing.decision_finalization_id != finalization.id or existing.decision_cutoff_period != cutoff:
                    raise DecisionSnapshotReferenceError("execution Decision scope is already linked to different immutable provenance")
                return self._view(existing)
            row = BusinessWorkflowDecisionSnapshotReference(
                company_id=company_id, execution_id=execution_id, decision_finalization_id=finalization.id,
                decision_snapshot_id=snapshot.id, material_code=material_code, demand_type=demand_type,
                decision_context=context, decision_cutoff_period=cutoff,
            )
            session.add(row)
            try:
                session.commit()
                return self._view(row)
            except IntegrityError:
                session.rollback()
                existing = session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(
                    company_id=company_id, execution_id=execution_id, material_code=material_code,
                    demand_type=demand_type, decision_context=context,
                ).one()
                if existing.decision_snapshot_id != snapshot.id:
                    raise DecisionSnapshotReferenceError("concurrent association disagrees with Snapshot provenance")
                return self._view(existing)
        finally:
            session.close()

    def list_for_execution(self, company_id, execution_id):
        """Read-only historical lookup; no Resolver, Policy, or current memory access."""
        session = self._sf()
        try:
            rows = session.query(BusinessWorkflowDecisionSnapshotReference).filter_by(
                company_id=company_id, execution_id=execution_id
            ).order_by(
                BusinessWorkflowDecisionSnapshotReference.material_code,
                BusinessWorkflowDecisionSnapshotReference.demand_type,
                BusinessWorkflowDecisionSnapshotReference.decision_context,
            ).all()
            return tuple(self._view(row) for row in rows)
        finally:
            session.close()
