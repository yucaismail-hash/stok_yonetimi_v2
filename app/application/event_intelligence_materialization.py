"""Durable current projection of EventAssociationService results; no analytical duplication."""
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.application.event_association import EventAssociationService
from app.database import SessionLocal
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.services.dataset.weekly_normalization import parse_weekly_period


@dataclass(frozen=True)
class EventIntelligenceMaterializationResult:
    status: str
    memory_id: object | None
    row_version: int | None
    source_fingerprint: str | None


class EventIntelligenceMaterializationService:
    def __init__(self, session_factory=SessionLocal, association_service=None):
        self._sf = session_factory; self._association = association_service or EventAssociationService(session_factory)

    def materialize(self, company_id, material_code, demand_type, event_identity, cutoff, *, as_of=None, reconcile_existing_insufficient=False):
        # A current projection defaults to the present read boundary. Historical
        # replay callers may still supply an explicit as_of value.
        result = self._association.calculate(company_id, material_code, demand_type, event_identity, cutoff, as_of=as_of or datetime.now(timezone.utc))
        s = self._sf()
        try:
            if result.classification == "INSUFFICIENT_EVIDENCE":
                if not reconcile_existing_insufficient:
                    return EventIntelligenceMaterializationResult("NOT_MATERIALIZED", None, None, result.source_fingerprint)
                current = s.query(EventIntelligenceMemory).filter_by(
                    company_id=company_id,
                    material_code=material_code,
                    demand_type=demand_type,
                    event_identity=event_identity,
                ).one_or_none()
                if current is None:
                    return EventIntelligenceMaterializationResult("NOT_MATERIALIZED", None, None, result.source_fingerprint)
            return self.persist_result(s, result)
        except IntegrityError:
            s.rollback(); return self._recover(company_id, material_code, demand_type, event_identity, result.cutoff_period)
        except Exception:
            s.rollback(); raise
        finally: s.close()

    def get_current(self, company_id, material_code, demand_type, event_identity):
        s = self._sf()
        try: return s.query(EventIntelligenceMemory).filter_by(company_id=company_id, material_code=material_code, demand_type=demand_type, event_identity=event_identity).one_or_none()
        finally: s.close()

    def list_current(self, company_id, *, material_code=None, demand_type=None):
        s = self._sf()
        try:
            q=s.query(EventIntelligenceMemory).filter_by(company_id=company_id)
            if material_code is not None:q=q.filter_by(material_code=material_code)
            if demand_type is not None:q=q.filter_by(demand_type=demand_type)
            return tuple(q.order_by(EventIntelligenceMemory.material_code,EventIntelligenceMemory.demand_type,EventIntelligenceMemory.event_identity).all())
        finally:s.close()

    def persist_result(self, s, result):
        current=s.query(EventIntelligenceMemory).filter_by(company_id=result.company_id,material_code=result.material_code,demand_type=result.demand_type,event_identity=result.event_identity).with_for_update().one_or_none()
        if current and parse_weekly_period(result.cutoff_period).period < parse_weekly_period(current.cutoff_period).period:
            return EventIntelligenceMaterializationResult("STALE_RESULT",current.id,current.row_version,current.source_fingerprint)
        values=self._values(result)
        if current:
            if current.source_fingerprint==result.source_fingerprint:return EventIntelligenceMaterializationResult("UNCHANGED",current.id,current.row_version,current.source_fingerprint)
            for key,value in values.items():setattr(current,key,value)
            current.row_version+=1;s.commit();return EventIntelligenceMaterializationResult("UPDATED",current.id,current.row_version,current.source_fingerprint)
        current=EventIntelligenceMemory(company_id=result.company_id,material_code=result.material_code,demand_type=result.demand_type,event_identity=result.event_identity,row_version=1,**values)
        s.add(current);s.commit();return EventIntelligenceMaterializationResult("CREATED",current.id,1,current.source_fingerprint)

    @staticmethod
    def _values(r):
        return dict(event_type_snapshot=r.event_type_snapshot,product_level=r.product_level,product_group=r.product_group,product_class=r.product_class,
            feature_schema_version=r.feature_schema_version,baseline_policy_version=r.baseline_policy_version,lag_policy_version=r.lag_policy_version,association_policy_version=r.association_policy_version,confidence_policy_version=r.confidence_policy_version,
            classification=r.classification,confidence=r.confidence,occurrence_count=r.occurrence_count,included_occurrence_ids=list(r.included_occurrence_ids),included_revision_ids=list(r.included_revision_ids),cutoff_period=r.cutoff_period,
            baseline_method=r.baseline_method,baseline_source_vintage_ids=list(r.baseline_source_vintage_ids),baseline_source_periods=list(r.baseline_source_periods),event_actual_mean=r.event_actual_mean,baseline_mean=r.baseline_mean,absolute_effect=r.absolute_effect,relative_effect=r.relative_effect,
            pre_event_mean=r.pre_event_mean,post_event_mean=r.post_event_mean,pre_change=r.pre_change,post_decay=r.post_decay,strongest_lag_weeks=r.strongest_lag_weeks,strongest_lag_relative_effect=r.strongest_lag_relative_effect,
            mean_relative_effect=r.mean_relative_effect,median_relative_effect=r.median_relative_effect,effect_dispersion=r.effect_dispersion,direction_consistency=r.direction_consistency,overlap_confounded=r.overlap_confounded,confounded_occurrence_ids=list(r.confounded_occurrence_ids),
            source_actual_observation_ids=list(r.actual_observation_ids),source_actual_revision_ids=list(r.actual_revision_ids),source_fingerprint=r.source_fingerprint,
            source_scope_metadata={"event_scopes":list(r.source_event_scope_metadata),"event_type":r.event_type_snapshot,"product_level":r.product_level,"product_group":r.product_group,"product_class":r.product_class})

    def _recover(self, company_id, material_code, demand_type, event_identity, cutoff_period):
        current=self.get_current(company_id,material_code,demand_type,event_identity)
        if current is None: raise
        status="UNCHANGED" if current.cutoff_period==parse_weekly_period(cutoff_period).period else "STALE_RESULT"
        return EventIntelligenceMaterializationResult(status,current.id,current.row_version,current.source_fingerprint)
