"""Compact, historical presentation contracts for completed Business Workflows."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ExecutionPresentation(BaseModel):
    execution_id: UUID
    status: str
    progress: float
    current_stage: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    dataset_id: UUID
    workflow_id: str
    failure_summary: str | None = None


class AggregatePresentation(BaseModel):
    result_reference_id: UUID
    result_type: str
    result_version: str
    contract_version: str
    validation_status: str
    created_at: datetime
    available_result_types: tuple[str, ...]


class AnalysisCoveragePresentation(BaseModel):
    total_scope_count: int
    fully_analyzed_count: int
    partially_analyzed_count: int
    excluded_count: int
    exclusions: tuple[dict[str, Any], ...]


class DecisionFinalizationPresentation(BaseModel):
    id: UUID
    status: str
    attempt_count: int
    completed_material_codes: tuple[str, ...]
    limitations: tuple[dict[str, Any], ...]
    finalized_at: datetime | None


class DecisionAssociationPresentation(BaseModel):
    id: UUID
    decision_snapshot_id: UUID
    material_code: str
    demand_type: str
    decision_context: str
    decision_cutoff_period: str


class DecisionSnapshotPresentation(BaseModel):
    id: UUID
    status: str
    agreement_status: str
    confidence: float
    decision_policy_version: str
    confidence_policy_version: str
    generated_at: datetime
    uncertainty_codes: tuple[str, ...]


class DecisionCandidatePresentation(BaseModel):
    ordinal: int
    candidate_type: str
    severity: str
    priority: int
    reason_codes: tuple[str, ...]
    supporting_evidence: tuple[Any, ...]
    conflicting_evidence: tuple[Any, ...]
    confidence: float
    expected_impact_references: tuple[Any, ...]
    what_would_change_this: tuple[Any, ...]


class DecisionExplanationSourcePresentation(BaseModel):
    group: str
    source: str
    semantic_type: str
    evidence: Any


class DecisionExplanationPresentation(BaseModel):
    decision: dict[str, Any]
    limitations: tuple[str, ...]
    source_provenance: tuple[DecisionExplanationSourcePresentation, ...]
    explanation_fingerprint: str


class DecisionPresentationItem(BaseModel):
    association: DecisionAssociationPresentation
    snapshot: DecisionSnapshotPresentation
    candidates: tuple[DecisionCandidatePresentation, ...]
    explanation: DecisionExplanationPresentation


class BusinessWorkflowDecisionPresentationResponse(BaseModel):
    execution: ExecutionPresentation
    aggregate: AggregatePresentation | None
    decision_finalization: DecisionFinalizationPresentation | None
    decisions: tuple[DecisionPresentationItem, ...]
    analysis_coverage: AnalysisCoveragePresentation | None = None
