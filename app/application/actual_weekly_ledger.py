"""Application boundary for canonical weekly actual ingestion and correction approval."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.dataset import Dataset, DatasetVersion
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


class ActualWeeklyLedgerError(ValueError): pass

_LEVELS = {
    "finished_good": "finished_good", "semi_finished_good": "semi_finished_good", "raw_material": "raw_material",
    "Mamul": "finished_good", "Yarı Mamul": "semi_finished_good", "Hammadde": "raw_material",
}


class ActualWeeklyLedgerService:
    def __init__(self, session_factory=SessionLocal): self._session_factory = session_factory

    @staticmethod
    def _quantity(value):
        if isinstance(value, bool): raise ActualWeeklyLedgerError("quantity must be numeric")
        try: result = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc: raise ActualWeeklyLedgerError("quantity must be numeric") from exc
        if not result.is_finite(): raise ActualWeeklyLedgerError("quantity must be finite")
        return result

    @staticmethod
    def _row(row, demand_type):
        if not isinstance(row, dict) or not isinstance(row.get("material_code"), str) or not row["material_code"]:
            raise ActualWeeklyLedgerError("material_code is required")
        try: period = parse_weekly_period(row.get("period")).period
        except ValueError as exc: raise ActualWeeklyLedgerError(str(exc)) from exc
        level = _LEVELS.get(row.get("product_level"))
        if not level: raise ActualWeeklyLedgerError("valid product_level is required")
        return {"material_code": row["material_code"], "period": period, "demand_type": demand_type, "quantity": ActualWeeklyLedgerService._quantity(row.get("quantity")), "product_level": level, "product_group": row.get("product_group"), "product_class": row.get("product_class")}

    def ingest_dataset_actuals(self, company_id, actor_user_id, dataset_id, rows, demand_type):
        session = self._session_factory()
        try:
            summary = self.ingest_dataset_actuals_in_session(session, company_id, actor_user_id, dataset_id, rows, demand_type)
            session.commit(); return summary
        except Exception:
            session.rollback(); raise
        finally: session.close()

    def approve_revision(self, company_id, revision_id, actor_user_id):
        return self._decide(company_id, revision_id, actor_user_id, True)

    def ingest_dataset_actuals_in_session(self, session, company_id, actor_user_id, dataset_id, rows, demand_type):
        """Write ledger evidence in the caller's transaction; never commits."""
        demand_type = validate_demand_type(demand_type)
        if demand_type is None: raise ActualWeeklyLedgerError("demand_type is required")
        dataset = session.query(Dataset).filter_by(id=dataset_id, company_id=company_id, user_id=actor_user_id).one_or_none()
        if not dataset: raise ActualWeeklyLedgerError("authorized source dataset is unavailable")
        version = session.query(DatasetVersion).filter_by(dataset_id=dataset_id, is_current=True).one_or_none()
        summary = {"new": 0, "noop": 0, "proposed": 0, "revision_ids": []}
        for incoming in rows:
            value = self._row(incoming, demand_type)
            observation = session.query(ActualWeeklyObservation).filter_by(company_id=company_id, material_code=value["material_code"], period=value["period"], demand_type=demand_type).one_or_none()
            common = {**value, "source_dataset_id": dataset.id, "source_dataset_version_id": version.id if version else None}
            revision_common = {key: item for key, item in common.items() if key != "quantity"}
            if observation is None:
                observation = ActualWeeklyObservation(company_id=company_id, **common); session.add(observation); session.flush()
                revision = ActualWeeklyRevision(company_id=company_id, observation_id=observation.id, previous_quantity=None, proposed_quantity=value["quantity"], change_type="new", approval_status="accepted", actor_user_id=actor_user_id, approved_by_user_id=actor_user_id, approved_at=datetime.now(timezone.utc), **revision_common)
                session.add(revision); session.flush(); summary["new"] += 1; summary["revision_ids"].append(str(revision.id))
            elif observation.quantity == value["quantity"]:
                summary["noop"] += 1
            else:
                revision = session.query(ActualWeeklyRevision).filter_by(company_id=company_id, observation_id=observation.id, proposed_quantity=value["quantity"], source_dataset_id=dataset.id, approval_status="proposed").one_or_none()
                if revision is None:
                    revision = ActualWeeklyRevision(company_id=company_id, observation_id=observation.id, previous_quantity=observation.quantity, proposed_quantity=value["quantity"], change_type="correction", approval_status="proposed", actor_user_id=actor_user_id, **revision_common)
                    session.add(revision); session.flush(); summary["proposed"] += 1
                summary["revision_ids"].append(str(revision.id))
        return summary

    def approve_revision_in_session(self, session, company_id, revision_id, actor_user_id):
        """Approve a known proposed revision without taking transaction ownership."""
        revision = session.query(ActualWeeklyRevision).filter_by(id=revision_id, company_id=company_id).one_or_none()
        if not revision or revision.approval_status != "proposed": raise ActualWeeklyLedgerError("pending revision is unavailable")
        revision.approval_status = "accepted"; revision.approved_by_user_id = actor_user_id; revision.approved_at = datetime.now(timezone.utc)
        observation = session.query(ActualWeeklyObservation).filter_by(id=revision.observation_id, company_id=company_id).one()
        observation.quantity = revision.proposed_quantity; observation.product_level = revision.product_level; observation.product_group = revision.product_group; observation.product_class = revision.product_class; observation.source_dataset_id = revision.source_dataset_id; observation.source_dataset_version_id = revision.source_dataset_version_id; observation.accepted_at = revision.approved_at
        session.flush()
        return str(revision.id)

    def reject_revision(self, company_id, revision_id, actor_user_id):
        return self._decide(company_id, revision_id, actor_user_id, False)

    def _decide(self, company_id, revision_id, actor_user_id, approved):
        session = self._session_factory()
        try:
            if approved:
                result = self.approve_revision_in_session(session, company_id, revision_id, actor_user_id)
            else:
                revision = session.query(ActualWeeklyRevision).filter_by(id=revision_id, company_id=company_id).one_or_none()
                if not revision or revision.approval_status != "proposed": raise ActualWeeklyLedgerError("pending revision is unavailable")
                revision.approval_status = "rejected"; revision.approved_by_user_id = actor_user_id; revision.rejected_at = datetime.now(timezone.utc); result = str(revision.id)
            session.commit(); return result
        except Exception:
            session.rollback(); raise
        finally: session.close()

    def list_observations(self, company_id):
        session = self._session_factory()
        try: return session.query(ActualWeeklyObservation).filter_by(company_id=company_id).order_by(ActualWeeklyObservation.material_code, ActualWeeklyObservation.period, ActualWeeklyObservation.demand_type).all()
        finally: session.close()
