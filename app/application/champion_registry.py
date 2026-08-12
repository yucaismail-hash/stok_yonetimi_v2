"""Bootstrap-only Champion Registry service; it never changes Forecast selection."""
import hashlib
import json

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.services.dataset.ingestion_policy import validate_demand_type


CLASSICAL_STRATEGY = "demand_forecaster_auto_v1"


class ChampionRegistryService:
    def __init__(self, session_factory=SessionLocal): self._session_factory = session_factory

    def bootstrap(self, company_id, material_code, demand_type, product_level=None, product_group=None, product_class=None):
        if not isinstance(material_code, str) or not material_code: raise ValueError("material_code is required")
        demand_type = validate_demand_type(demand_type)
        session = self._session_factory()
        try:
            current = self._current(session, company_id, material_code, demand_type)
            if current is not None: return current
            fingerprint = self._fingerprint(company_id, material_code, demand_type)
            entry = ChampionRegistryEntry(company_id=company_id, material_code=material_code, demand_type=demand_type, entry_type="classical_existing", classical_strategy=CLASSICAL_STRATEGY, product_level=product_level, product_group=product_group, product_class=product_class, provenance={"forecast_adapter": "forecast_adapter_v1", "forecast_contract": "DemandForecaster.auto"})
            session.add(entry); session.flush()
            session.add(ChampionRegistryTransition(company_id=company_id, material_code=material_code, demand_type=demand_type, transition_type="BOOTSTRAP", source_entry_id=None, destination_entry_id=entry.id, source_decision_id=None, expected_current_entry_id=None, reason="initial classical Champion bootstrap", idempotency_fingerprint=fingerprint))
            session.add(ChampionRegistryCurrent(company_id=company_id, material_code=material_code, demand_type=demand_type, active_entry_id=entry.id, row_version=1))
            session.commit()
            return self._current(session, company_id, material_code, demand_type)
        except IntegrityError:
            session.rollback()
            current = self._current(session, company_id, material_code, demand_type)
            if current is None: raise
            return current
        except Exception:
            session.rollback(); raise
        finally: session.close()

    def get_current(self, company_id, material_code, demand_type):
        session = self._session_factory()
        try: return self._current(session, company_id, material_code, validate_demand_type(demand_type))
        finally: session.close()

    def get_entry(self, company_id, entry_id):
        session = self._session_factory()
        try: return session.query(ChampionRegistryEntry).filter_by(id=entry_id, company_id=company_id).one_or_none()
        finally: session.close()

    @staticmethod
    def _current(session, company_id, material_code, demand_type):
        return session.query(ChampionRegistryCurrent).filter_by(company_id=company_id, material_code=material_code, demand_type=demand_type).one_or_none()

    @staticmethod
    def _fingerprint(company_id, material_code, demand_type):
        return hashlib.sha256(json.dumps([str(company_id), material_code, demand_type, "BOOTSTRAP"], separators=(",", ":")).encode()).hexdigest()
