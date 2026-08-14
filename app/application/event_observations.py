"""Canonical Event Observation write/read boundary; no Event Intelligence calculation."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
import json

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.company import User
from app.models.event_observation import EventObservation, EventRevision
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


SCOPE_TYPES = {"MATERIAL", "PRODUCT_GROUP", "PRODUCT_CLASS", "COMPANY"}
AUTHORITY_TYPES = {"COMPANY_EXPLICIT", "PUBLIC_REFERENCE"}
SOURCE_SYSTEMS = {"company_event", "public_calendar"}


class EventObservationError(ValueError): pass


@dataclass(frozen=True)
class EventObservationWriteResult:
    status: str; event_id: object; source_identity_fingerprint: str; current_evidence_fingerprint: str

@dataclass(frozen=True)
class EventRevisionResult:
    status: str; revision_id: object; event_id: object; current_evidence_fingerprint: str

def _json(value):
    if isinstance(value, (date, datetime)): return value.isoformat()
    return str(value) if value is not None and not isinstance(value, (str, int, float, bool, list, dict, tuple)) else value
def _digest(value): return sha256(json.dumps(value, default=_json, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class EventObservationService:
    """Company-scoped facts only: no dataset backfill, learning, Forecast, or workflow activity."""
    def __init__(self, session_factory=SessionLocal): self._sf=session_factory

    def create(self, company_id, *, event_identity, event_type, source_occurrence_reference, scope_type, demand_type,
               start_date, end_date, authority_type, source_system, scope_value=None, public_reference_id=None, provenance=None):
        payload=self._normalize(event_identity,event_type,source_occurrence_reference,scope_type,scope_value,demand_type,start_date,end_date,authority_type,source_system,public_reference_id,provenance)
        s=self._sf()
        try:
            identity=_digest({"company_id":company_id,"event_identity":payload["event_identity"],"source_occurrence_reference":payload["source_occurrence_reference"],"source_system":payload["source_system"]})
            existing=s.query(EventObservation).filter_by(company_id=company_id,source_identity_fingerprint=identity).one_or_none()
            fp=_digest(payload)
            if existing:
                if existing.current_evidence_fingerprint!=fp: raise EventObservationError("EVENT_CORRECTION_REQUIRED")
                return EventObservationWriteResult("ALREADY_EXISTS",existing.id,identity,existing.current_evidence_fingerprint)
            accepted_at=datetime.now(timezone.utc)
            row=EventObservation(company_id=company_id,source_identity_fingerprint=identity,current_evidence_fingerprint=fp,current_accepted_at=accepted_at,**payload)
            s.add(row);s.flush()
            # The initial accepted snapshot is the temporal anchor for as-of
            # reconstruction after mutable current columns are superseded.
            initial_snapshot={key:_json(value) for key,value in payload.items() if key not in {"start_period","end_period"}}
            base=EventRevision(company_id=company_id,event_observation_id=row.id,approval_status="accepted",
                previous_snapshot=initial_snapshot,proposed_snapshot=initial_snapshot,previous_evidence_fingerprint=fp,
                proposed_evidence_fingerprint=fp,correction_fingerprint=_digest({"event_id":row.id,"base":fp}),approved_at=accepted_at)
            s.add(base);s.flush();row.current_revision_id=base.id
            try:
                s.commit();return EventObservationWriteResult("CREATED",row.id,identity,row.current_evidence_fingerprint)
            except IntegrityError:
                s.rollback();existing=s.query(EventObservation).filter_by(company_id=company_id,source_identity_fingerprint=identity).one_or_none()
                if existing is None: raise
                if existing.current_evidence_fingerprint!=fp: raise EventObservationError("EVENT_CORRECTION_REQUIRED")
                return EventObservationWriteResult("ALREADY_EXISTS",existing.id,identity,existing.current_evidence_fingerprint)
        except IntegrityError:
            s.rollback();existing=s.query(EventObservation).filter_by(company_id=company_id,source_identity_fingerprint=identity).one_or_none()
            if existing is None: raise
            if existing.current_evidence_fingerprint!=fp: raise EventObservationError("EVENT_CORRECTION_REQUIRED")
            return EventObservationWriteResult("ALREADY_EXISTS",existing.id,identity,existing.current_evidence_fingerprint)
        except Exception: s.rollback();raise
        finally:s.close()

    def propose_correction(self, company_id,event_id,actor_user_id,**changes):
        s=self._sf()
        try:
            event=self._event(s,company_id,event_id);self._actor(s,company_id,actor_user_id)
            allowed={"event_identity","event_type","scope_type","scope_value","demand_type","start_date","end_date","authority_type","source_system","public_reference_id","provenance","status"}
            if set(changes)-allowed: raise EventObservationError("EVENT_CORRECTION_FIELD_UNSUPPORTED")
            previous=self._snapshot(event);candidate={**previous,**changes}
            for field in ("start_date", "end_date"):
                if isinstance(candidate.get(field), str): candidate[field] = date.fromisoformat(candidate[field])
            payload=self._normalize(**candidate)
            proposed_fp=_digest(payload);correction_fp=_digest({"event_id":event.id,"previous":event.current_evidence_fingerprint,"proposed":proposed_fp})
            old=s.query(EventRevision).filter_by(company_id=company_id,correction_fingerprint=correction_fp).one_or_none()
            if old:return EventRevisionResult("ALREADY_EXISTS",old.id,event.id,old.proposed_evidence_fingerprint)
            proposed_snapshot={key:_json(value) for key,value in payload.items() if key not in {"start_period","end_period"}}
            row=EventRevision(company_id=company_id,event_observation_id=event.id,actor_user_id=actor_user_id,previous_snapshot=previous,proposed_snapshot=proposed_snapshot,previous_evidence_fingerprint=event.current_evidence_fingerprint,proposed_evidence_fingerprint=proposed_fp,correction_fingerprint=correction_fp)
            s.add(row);s.commit();return EventRevisionResult("PROPOSED",row.id,event.id,proposed_fp)
        except Exception:s.rollback();raise
        finally:s.close()

    def accept_correction(self,company_id,revision_id,actor_user_id):return self._decide(company_id,revision_id,actor_user_id,True)
    def reject_correction(self,company_id,revision_id,actor_user_id):return self._decide(company_id,revision_id,actor_user_id,False)
    def cancel(self,company_id,event_id,actor_user_id):
        proposed=self.propose_correction(company_id,event_id,actor_user_id,status="CANCELLED")
        return self.accept_correction(company_id,proposed.revision_id,actor_user_id) if proposed.status=="PROPOSED" else proposed
    def get(self,company_id,event_id):
        s=self._sf()
        try:return s.query(EventObservation).filter_by(company_id=company_id,id=event_id).one_or_none()
        finally:s.close()
    def query_current(self,company_id,*,demand_type=None,start_date=None,end_date=None,scope_type=None,scope_value=None,event_identity=None,event_type=None):
        s=self._sf()
        try:
            q=s.query(EventObservation).filter_by(company_id=company_id)
            if demand_type:q=q.filter_by(demand_type=validate_demand_type(demand_type))
            if scope_type:q=q.filter_by(scope_type=scope_type)
            if scope_value is not None:q=q.filter_by(scope_value=scope_value)
            if event_identity:q=q.filter_by(event_identity=event_identity)
            if event_type:q=q.filter_by(event_type=event_type)
            if start_date:q=q.filter(EventObservation.end_date>=start_date)
            if end_date:q=q.filter(EventObservation.start_date<=end_date)
            return tuple(q.order_by(EventObservation.start_date,EventObservation.id).all())
        finally:s.close()
    def as_of(self,company_id,event_id,as_of):
        s=self._sf()
        try:
            event=self._event(s,company_id,event_id);accepted=s.query(EventRevision).filter_by(company_id=company_id,event_observation_id=event_id,approval_status="accepted").filter(EventRevision.approved_at<=as_of).order_by(EventRevision.approved_at,EventRevision.id).all()
            if event.current_accepted_at<=as_of and not accepted:return self._snapshot(event)
            if not accepted:return None
            return accepted[-1].proposed_snapshot
        finally:s.close()

    def _decide(self,company_id,revision_id,actor_user_id,accepted):
        s=self._sf()
        try:
            self._actor(s,company_id,actor_user_id);r=s.query(EventRevision).filter_by(company_id=company_id,id=revision_id).with_for_update().one_or_none()
            if r is None or r.approval_status!="proposed":raise EventObservationError("EVENT_PENDING_REVISION_UNAVAILABLE")
            event=self._event(s,company_id,r.event_observation_id)
            if accepted:
                if event.current_evidence_fingerprint!=r.previous_evidence_fingerprint:raise EventObservationError("EVENT_CORRECTION_STALE")
                self._apply(event,r.proposed_snapshot,r.proposed_evidence_fingerprint);r.approval_status="accepted";r.approved_at=datetime.now(timezone.utc);event.current_revision_id=r.id;event.current_accepted_at=r.approved_at;status="ACCEPTED"
            else:r.approval_status="rejected";r.rejected_at=datetime.now(timezone.utc);status="REJECTED"
            s.commit();return EventRevisionResult(status,r.id,event.id,event.current_evidence_fingerprint)
        except Exception:s.rollback();raise
        finally:s.close()
    @staticmethod
    def _event(s,cid,eid):
        row=s.query(EventObservation).filter_by(company_id=cid,id=eid).one_or_none()
        if row is None:raise LookupError("EVENT_OBSERVATION_NOT_FOUND")
        return row
    @staticmethod
    def _actor(s,cid,uid):
        if s.query(User).filter_by(id=uid,company_id=cid).one_or_none() is None:raise EventObservationError("EVENT_ACTOR_UNAUTHORIZED")
    @staticmethod
    def _date(value,name):
        if not isinstance(value,date) or isinstance(value,datetime):raise EventObservationError(name+" must be a date")
        return value
    def _normalize(self,event_identity,event_type,source_occurrence_reference,scope_type,scope_value,demand_type,start_date,end_date,authority_type,source_system,public_reference_id,provenance,status="ACTIVE"):
        if not all(isinstance(x,str) and x for x in (event_identity,event_type,source_occurrence_reference)):raise EventObservationError("EVENT_IDENTITY_REQUIRED")
        if scope_type not in SCOPE_TYPES:raise EventObservationError("EVENT_SCOPE_UNSUPPORTED")
        if (scope_type=="COMPANY") != (scope_value is None):raise EventObservationError("EVENT_SCOPE_VALUE_INVALID")
        if scope_type!="COMPANY" and (not isinstance(scope_value,str) or not scope_value):raise EventObservationError("EVENT_SCOPE_VALUE_REQUIRED")
        demand=validate_demand_type(demand_type)
        if demand is None:raise EventObservationError("EVENT_DEMAND_TYPE_REQUIRED")
        start=self._date(start_date,"start_date");end=self._date(end_date,"end_date")
        if end<start:raise EventObservationError("EVENT_DATE_RANGE_INVALID")
        if authority_type not in AUTHORITY_TYPES or source_system not in SOURCE_SYSTEMS:raise EventObservationError("EVENT_AUTHORITY_UNSUPPORTED")
        if authority_type=="PUBLIC_REFERENCE" and (not isinstance(public_reference_id,str) or not public_reference_id):raise EventObservationError("EVENT_PUBLIC_REFERENCE_REQUIRED")
        if authority_type=="COMPANY_EXPLICIT" and public_reference_id is not None:raise EventObservationError("EVENT_PUBLIC_REFERENCE_INVALID")
        if status not in {"ACTIVE","CANCELLED"}:raise EventObservationError("EVENT_STATUS_UNSUPPORTED")
        if provenance is None:provenance={}
        if not isinstance(provenance,dict):raise EventObservationError("EVENT_PROVENANCE_INVALID")
        return {"event_identity":event_identity,"event_type":event_type,"source_occurrence_reference":source_occurrence_reference,"scope_type":scope_type,"scope_value":scope_value,"demand_type":demand,"start_date":start,"end_date":end,"start_period":self._period(start),"end_period":self._period(end),"authority_type":authority_type,"source_system":source_system,"public_reference_id":public_reference_id,"provenance":provenance,"status":status}
    @staticmethod
    def _period(value):return f"{value.isocalendar().year:04d}-W{value.isocalendar().week:02d}"
    @staticmethod
    def _snapshot(event):
        return {key:_json(getattr(event,key)) for key in ("event_identity","event_type","source_occurrence_reference","scope_type","scope_value","demand_type","start_date","end_date","authority_type","source_system","public_reference_id","provenance","status")}
    def _apply(self,event,snapshot,fingerprint):
        payload=self._normalize(**{**snapshot,"start_date":date.fromisoformat(snapshot["start_date"]),"end_date":date.fromisoformat(snapshot["end_date"])})
        for key,value in payload.items():setattr(event,key,value)
        event.current_evidence_fingerprint=fingerprint
