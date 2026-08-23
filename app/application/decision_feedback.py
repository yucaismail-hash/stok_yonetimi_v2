"""Company-scoped append-only user opinion events for immutable Decision Snapshots."""
from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from time import perf_counter

from app.database import SessionLocal
from app.models.company import User
from app.models.decision_feedback import DecisionFeedbackEvent
from app.models.decision_snapshot import DecisionSnapshot, DecisionSnapshotCandidate


@dataclass(frozen=True)
class DecisionFeedbackResult:
    status: str
    feedback_id: object
    elapsed_ms: float


class DecisionFeedbackService:
    """Feedback is opinion/audit evidence only; no Learning, approval, or action writes occur here."""
    _TYPES = {"HELPFUL", "NOT_HELPFUL"}
    _MAX_COMMENT = 1000
    def __init__(self, session_factory=SessionLocal): self._sf = session_factory

    @staticmethod
    def _fingerprint(user_id, snapshot_id, ordinal, candidate_type, feedback_type, comment):
        value = (str(user_id), str(snapshot_id), ordinal, candidate_type, feedback_type, comment or "")
        return sha256(dumps(value, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _event(row):
        return {"feedback_id": str(row.id), "company_id": str(row.company_id), "user_id": str(row.user_id),
            "decision_snapshot_id": str(row.decision_snapshot_id), "candidate_ordinal": row.candidate_ordinal,
            "candidate_type": row.candidate_type, "feedback_type": row.feedback_type, "comment": row.comment,
            "source_metadata": row.source_metadata or {}, "supersedes_feedback_id": str(row.supersedes_feedback_id) if row.supersedes_feedback_id else None,
            "created_at": row.created_at.isoformat()}

    def record(self, company_id, user_id, decision_snapshot_id, feedback_type, *, candidate_ordinal=None, candidate_type=None, comment=None, source_metadata=None, supersedes_feedback_id=None):
        started = perf_counter()
        if feedback_type not in self._TYPES: raise ValueError("invalid feedback_type")
        if comment is not None and (not isinstance(comment, str) or len(comment) > self._MAX_COMMENT): raise ValueError("comment must be a string of at most 1000 characters")
        session = self._sf()
        try:
            user = session.query(User).filter_by(id=user_id, company_id=company_id).one_or_none()
            snapshot = session.query(DecisionSnapshot).filter_by(id=decision_snapshot_id, company_id=company_id).one_or_none()
            if user is None or snapshot is None: raise ValueError("company-scoped user or snapshot not found")
            if candidate_ordinal is not None:
                candidate = session.query(DecisionSnapshotCandidate).filter_by(decision_snapshot_id=snapshot.id, ordinal=candidate_ordinal).one_or_none()
                if candidate is None or (candidate_type is not None and candidate.candidate_type != candidate_type): raise ValueError("candidate does not belong to snapshot")
                candidate_type = candidate.candidate_type
            elif candidate_type is not None: raise ValueError("candidate_type requires candidate_ordinal")
            previous = None
            if supersedes_feedback_id is not None:
                previous = session.query(DecisionFeedbackEvent).filter_by(id=supersedes_feedback_id, company_id=company_id, user_id=user_id, decision_snapshot_id=snapshot.id).one_or_none()
                if previous is None: raise ValueError("superseded feedback does not belong to user and snapshot")
                if (previous.candidate_ordinal, previous.candidate_type) != (candidate_ordinal, candidate_type): raise ValueError("superseded feedback candidate mismatch")
            fingerprint = self._fingerprint(user_id, snapshot.id, candidate_ordinal, candidate_type, feedback_type, comment)
            duplicate = session.query(DecisionFeedbackEvent).filter_by(company_id=company_id, user_id=user_id, decision_snapshot_id=snapshot.id,
                candidate_ordinal=candidate_ordinal, candidate_type=candidate_type, feedback_type=feedback_type,
                feedback_fingerprint=fingerprint, supersedes_feedback_id=supersedes_feedback_id).one_or_none()
            if duplicate: return DecisionFeedbackResult("ALREADY_EXISTS", duplicate.id, (perf_counter()-started)*1000)
            event = DecisionFeedbackEvent(company_id=company_id, user_id=user_id, decision_snapshot_id=snapshot.id,
                candidate_ordinal=candidate_ordinal, candidate_type=candidate_type, feedback_type=feedback_type, comment=comment,
                source_metadata=source_metadata or {}, supersedes_feedback_id=supersedes_feedback_id, feedback_fingerprint=fingerprint)
            session.add(event); session.commit()
            return DecisionFeedbackResult("CREATED", event.id, (perf_counter()-started)*1000)
        finally: session.close()

    def list_for_snapshot(self, company_id, decision_snapshot_id):
        session = self._sf()
        try:
            if session.query(DecisionSnapshot.id).filter_by(id=decision_snapshot_id, company_id=company_id).one_or_none() is None: return None
            rows = session.query(DecisionFeedbackEvent).filter_by(company_id=company_id, decision_snapshot_id=decision_snapshot_id).order_by(DecisionFeedbackEvent.created_at, DecisionFeedbackEvent.id).all()
            events = tuple(self._event(row) for row in rows)
            latest = {}
            for event in events: latest[(event["user_id"], event["candidate_ordinal"], event["candidate_type"])] = event
            counts = {kind: sum(1 for event in events if event["feedback_type"] == kind) for kind in sorted(self._TYPES)}
            return {"events": events, "latest_by_user_candidate": tuple(latest[key] for key in sorted(latest, key=str)), "counts": counts}
        finally: session.close()
