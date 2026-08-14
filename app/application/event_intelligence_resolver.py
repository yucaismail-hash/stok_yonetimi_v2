"""Read-only, cutoff-safe Event Intelligence context resolution."""
from decimal import Decimal
from app.database import SessionLocal
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


class EventIntelligenceResolver:
    """Resolves compact, non-causal event context without refreshing memory."""
    def __init__(self, session_factory=SessionLocal): self._session_factory = session_factory

    def resolve(self, company_id, material_code, demand_type, analysis_cutoff_period):
        demand = validate_demand_type(demand_type)
        cutoff = parse_weekly_period(analysis_cutoff_period).period
        session = self._session_factory()
        try:
            rows = session.query(EventIntelligenceMemory).filter_by(
                company_id=company_id, material_code=material_code, demand_type=demand,
            ).order_by(EventIntelligenceMemory.event_identity).all()
            compatible = [row for row in rows if self._at_or_before(row.cutoff_period, cutoff)]
            if not compatible:
                return {"status": "EVENT_INTELLIGENCE_CUTOFF_INCOMPATIBLE" if rows else "EVENT_INTELLIGENCE_ABSENT",
                        "analysis_cutoff_period": cutoff, "memories": []}
            return {"status": "EVENT_INTELLIGENCE_AVAILABLE", "analysis_cutoff_period": cutoff,
                    "memories": [self._compact(row) for row in compatible]}
        finally:
            session.close()

    @staticmethod
    def _at_or_before(value, cutoff):
        left, right = parse_weekly_period(value), parse_weekly_period(cutoff)
        return (left.year, left.week) <= (right.year, right.week)

    @staticmethod
    def _value(value):
        return float(value) if isinstance(value, Decimal) else value

    @classmethod
    def _compact(cls, row):
        no_effect = row.classification == "INSUFFICIENT_EVIDENCE" or bool(row.overlap_confounded)
        return {
            "memory_id": str(row.id), "event_identity": row.event_identity,
            "event_type": row.event_type_snapshot, "classification": row.classification,
            "confidence": cls._value(row.confidence), "occurrence_count": row.occurrence_count,
            "baseline_method": row.baseline_method, "evidence_cutoff_period": row.cutoff_period,
            "source_fingerprint": row.source_fingerprint, "overlap_confounded": bool(row.overlap_confounded),
            "source_scope": (row.source_scope_metadata or {}).get("event_scopes", []),
            "absolute_association": None if no_effect else cls._value(row.absolute_effect),
            "relative_association": None if no_effect else cls._value(row.relative_effect),
            "association_language": "non_causal_historical_association",
        }
