"""Bounded refresh façade for durable Event Intelligence current projections."""
from dataclasses import dataclass
from time import perf_counter
from app.application.event_intelligence_materialization import EventIntelligenceMaterializationService
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period

@dataclass(frozen=True)
class EventIntelligenceRefreshResult:
    company_id: object; material_code: str; demand_type: str; event_identity: str; cutoff_period: str
    status: str; memory_id: object | None; previous_fingerprint: str | None; source_fingerprint: str | None
    previous_row_version: int | None; row_version: int | None; duration_ms: float

class EventIntelligenceRefreshService:
    """Refreshes exactly caller-authorized event-memory scopes; never discovers work."""
    def __init__(self, materialization_service=None): self._materializer=materialization_service or EventIntelligenceMaterializationService()
    def refresh(self, company_id, material_code, demand_type, event_identity, cutoff_period):
        started=perf_counter(); demand=validate_demand_type(demand_type); cutoff=parse_weekly_period(cutoff_period).period
        before=self._materializer.get_current(company_id,material_code,demand,event_identity)
        # Existing rows are explicitly reconciled to insufficient evidence when a
        # correction/cancellation removes their currently applicable occurrence.
        result=self._materializer.materialize(company_id,material_code,demand,event_identity,cutoff,reconcile_existing_insufficient=True)
        return EventIntelligenceRefreshResult(company_id,material_code,demand,event_identity,cutoff,result.status,result.memory_id,
            before.source_fingerprint if before else None,result.source_fingerprint,before.row_version if before else None,result.row_version,(perf_counter()-started)*1000)
    def refresh_batch(self, requests): return tuple(self.refresh(**request) for request in requests)
