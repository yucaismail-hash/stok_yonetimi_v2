"""Read-only, historical presentation composition for Business Workflows.

This boundary deliberately composes persisted Runtime and Decision vintages.  It
never materializes a Decision, resolves current evidence, or invokes analytics.
"""

from uuid import UUID

from app.application.business_workflow_decision_snapshot_reference import (
    BusinessWorkflowDecisionSnapshotReferenceService,
)
from app.application.decision_explanation import DecisionExplanationService
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore
from app.models.business_workflow_decision_finalization import (
    BusinessWorkflowDecisionFinalization,
)
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate
from app.schemas.business_workflow_presentation import (
    AggregatePresentation,
    AnalysisCoveragePresentation,
    BusinessWorkflowDecisionPresentationResponse,
    DecisionAssociationPresentation,
    DecisionCandidatePresentation,
    DecisionExplanationPresentation,
    DecisionExplanationSourcePresentation,
    DecisionFinalizationPresentation,
    DecisionPresentationItem,
    DecisionSnapshotPresentation,
    ExecutionPresentation,
)


class BusinessWorkflowPresentationNotFoundError(LookupError):
    """The company-scoped Business Workflow execution is unavailable."""


class BusinessWorkflowPresentationIntegrityError(RuntimeError):
    """Persisted execution Decision provenance is internally inconsistent."""


class BusinessWorkflowPresentationService:
    """Compose immutable, tenant-scoped presentation data without side effects."""

    def __init__(
        self,
        session_factory=SessionLocal,
        reference_service_factory=BusinessWorkflowDecisionSnapshotReferenceService,
        explanation_service_factory=DecisionExplanationService,
    ):
        self._sf = session_factory
        self._reference_service_factory = reference_service_factory
        self._explanation_service_factory = explanation_service_factory

    @staticmethod
    def _failure_summary(execution):
        failure = execution.terminal_error
        if isinstance(failure, dict):
            failure = failure.get("code")
        elif failure:
            failure = "WORKFLOW_EXECUTION_FAILED"
        return str(failure) if failure else None

    @staticmethod
    def _execution_view(execution):
        return ExecutionPresentation(
            execution_id=execution.execution_id,
            status=execution.state,
            progress=float(execution.progress),
            current_stage=execution.current_stage,
            created_at=execution.created_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            dataset_id=execution.dataset_id,
            workflow_id=execution.workflow_id,
            failure_summary=BusinessWorkflowPresentationService._failure_summary(execution),
        )

    @staticmethod
    def _aggregate_view(aggregate):
        if aggregate is None:
            return None
        provenance = aggregate.inline_result.get("provenance", {}) if isinstance(aggregate.inline_result, dict) else {}
        available = sorted(
            key.removesuffix("_result_reference_id")
            for key in provenance
            if key.endswith("_result_reference_id")
        )
        return AggregatePresentation(
            result_reference_id=aggregate.id,
            result_type=aggregate.result_type,
            result_version=aggregate.result_version,
            contract_version=aggregate.contract_version,
            validation_status=aggregate.validation_status,
            created_at=aggregate.created_at,
            available_result_types=tuple(available),
        )

    @staticmethod
    def _coverage_view(aggregate):
        if aggregate is None or not isinstance(aggregate.inline_result, dict):
            return None
        coverage = aggregate.inline_result.get("analysis_coverage")
        if not isinstance(coverage, dict):
            return None
        required = ("total_scope_count", "fully_analyzed_count", "partially_analyzed_count", "excluded_count")
        if not all(isinstance(coverage.get(field), int) and coverage[field] >= 0 for field in required):
            return None
        exclusions = coverage.get("exclusions")
        if not isinstance(exclusions, list) or not all(isinstance(item, dict) for item in exclusions):
            return None
        return AnalysisCoveragePresentation(**{field: coverage[field] for field in required}, exclusions=tuple(exclusions))

    @staticmethod
    def _finalization_view(row):
        if row is None:
            return None
        return DecisionFinalizationPresentation(
            id=row.id,
            status=row.status,
            attempt_count=row.attempt_count,
            completed_material_codes=tuple(row.completed_material_codes or ()),
            limitations=tuple(row.limitations or ()),
            finalized_at=row.finalized_at,
        )

    @staticmethod
    def _snapshot_view(snapshot):
        return DecisionSnapshotPresentation(
            id=snapshot.id,
            status=snapshot.status,
            agreement_status=snapshot.agreement_status,
            confidence=float(snapshot.confidence),
            decision_policy_version=snapshot.decision_policy_version,
            confidence_policy_version=snapshot.confidence_policy_version,
            generated_at=snapshot.generated_at,
            uncertainty_codes=tuple(snapshot.uncertainty_codes or ()),
        )

    @staticmethod
    def _candidate_view(candidate):
        return DecisionCandidatePresentation(
            ordinal=candidate.ordinal,
            candidate_type=candidate.candidate_type,
            severity=candidate.severity,
            priority=candidate.priority,
            reason_codes=tuple(candidate.reason_codes or ()),
            supporting_evidence=tuple(candidate.supporting_evidence or ()),
            conflicting_evidence=tuple(candidate.conflicting_evidence or ()),
            confidence=float(candidate.confidence),
            expected_impact_references=tuple(candidate.expected_impact_references or ()),
            what_would_change_this=tuple(candidate.what_would_change_this or ()),
        )

    @staticmethod
    def _explanation_view(explanation):
        return DecisionExplanationPresentation(
            decision=explanation.decision,
            limitations=explanation.limitations,
            source_provenance=tuple(
                DecisionExplanationSourcePresentation(**source)
                for source in explanation.source_provenance
            ),
            explanation_fingerprint=explanation.explanation_fingerprint,
        )

    def get(self, company_id: UUID, execution_id: UUID) -> BusinessWorkflowDecisionPresentationResponse:
        """Read one company-owned Business Workflow and its frozen Decision vintages."""
        session = self._sf()
        try:
            store = RuntimeStore(session)
            # Ownership and type are deliberately established before Decision reads.
            execution = store.get_execution(execution_id, company_id)
            if execution is None or execution.analysis_type != "business_workflow":
                raise BusinessWorkflowPresentationNotFoundError("Business Workflow execution was not found")

            aggregate = store.get_execution_aggregate_result(execution_id, company_id)
            finalization = session.query(BusinessWorkflowDecisionFinalization).filter_by(
                company_id=company_id, execution_id=execution_id
            ).one_or_none()
            execution_view = self._execution_view(execution)
            aggregate_view = self._aggregate_view(aggregate)
            coverage_view = self._coverage_view(aggregate)
            finalization_view = self._finalization_view(finalization)
        finally:
            session.close()

        references = self._reference_service_factory().list_for_execution(company_id, execution_id)
        decision_items = []
        session = self._sf()
        try:
            for reference in references:
                snapshot = session.query(DecisionSnapshot).filter_by(
                    id=reference.decision_snapshot_id, company_id=company_id
                ).one_or_none()
                if snapshot is None:
                    raise BusinessWorkflowPresentationIntegrityError(
                        "execution Decision association references an unavailable company Snapshot"
                    )
                scope = (
                    snapshot.material_code, snapshot.demand_type,
                    snapshot.decision_context, snapshot.decision_cutoff_period,
                )
                if scope != (
                    reference.material_code, reference.demand_type,
                    reference.decision_context, reference.decision_cutoff_period,
                ):
                    raise BusinessWorkflowPresentationIntegrityError(
                        "execution Decision association and Snapshot scope disagree"
                    )
                candidates = session.query(DecisionSnapshotCandidate).filter_by(
                    decision_snapshot_id=snapshot.id
                ).order_by(DecisionSnapshotCandidate.ordinal).all()
                explanation = self._explanation_service_factory().get(company_id, snapshot.id)
                if explanation is None:
                    raise BusinessWorkflowPresentationIntegrityError(
                        "company Snapshot explanation is unavailable"
                    )
                decision_items.append(DecisionPresentationItem(
                    association=DecisionAssociationPresentation(
                        id=reference.id,
                        decision_snapshot_id=reference.decision_snapshot_id,
                        material_code=reference.material_code,
                        demand_type=reference.demand_type,
                        decision_context=reference.decision_context,
                        decision_cutoff_period=reference.decision_cutoff_period,
                    ),
                    snapshot=self._snapshot_view(snapshot),
                    candidates=tuple(self._candidate_view(candidate) for candidate in candidates),
                    explanation=self._explanation_view(explanation),
                ))
        finally:
            session.close()

        return BusinessWorkflowDecisionPresentationResponse(
            execution=execution_view,
            aggregate=aggregate_view,
            decision_finalization=finalization_view,
            decisions=tuple(decision_items),
            analysis_coverage=coverage_view,
        )
