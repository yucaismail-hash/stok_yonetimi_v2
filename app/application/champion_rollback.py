"""Explicit, PostgreSQL-atomic Champion rollback governance operation."""
import hashlib
from dataclasses import dataclass
from xgboost.core import XGBoostError

from app.application.xgboost_challenger_artifacts import ArtifactIntegrityError, XGBoostChallengerArtifactService
from app.database import SessionLocal
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.services.dataset.ingestion_policy import validate_demand_type


@dataclass(frozen=True)
class ChampionRollbackResult:
    status: str
    active_entry_id: object | None
    transition_id: object | None


class ChampionRollbackService:
    """Moves a scoped current pointer only to an explicit known-good entry."""

    def __init__(self, session_factory=SessionLocal, artifact_service_factory=None):
        self._session_factory = session_factory
        self._artifact_service_factory = artifact_service_factory

    def rollback(self, company_id, material_code, demand_type, expected_current_champion_id, destination_champion_id, reason):
        if not isinstance(material_code, str) or not material_code:
            raise ValueError("material_code is required")
        demand_type = validate_demand_type(demand_type)
        if expected_current_champion_id is None or destination_champion_id is None:
            raise ValueError("expected_current_champion_id and destination_champion_id are required")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 256:
            raise ValueError("reason is required and must be at most 256 characters")
        fingerprint = hashlib.sha256(f"{company_id}:{material_code}:{demand_type}:{expected_current_champion_id}:{destination_champion_id}:{reason}:ROLLBACK".encode()).hexdigest()
        session = self._session_factory()
        try:
            # Fast idempotency path; repeated calls never need to move the pointer again.
            existing = session.query(ChampionRegistryTransition).filter_by(company_id=company_id, idempotency_fingerprint=fingerprint).one_or_none()
            if existing is not None:
                return ChampionRollbackResult("ALREADY_ROLLED_BACK", existing.destination_entry_id, existing.id)
            current = session.query(ChampionRegistryCurrent).filter_by(company_id=company_id, material_code=material_code, demand_type=demand_type).with_for_update().one_or_none()
            if current is None:
                return ChampionRollbackResult("REGISTRY_NOT_BOOTSTRAPPED", None, None)
            # Recheck after the PostgreSQL current-pointer lock for true cross-process idempotency.
            existing = session.query(ChampionRegistryTransition).filter_by(company_id=company_id, idempotency_fingerprint=fingerprint).one_or_none()
            if existing is not None:
                return ChampionRollbackResult("ALREADY_ROLLED_BACK", existing.destination_entry_id, existing.id)
            if current.active_entry_id != expected_current_champion_id:
                return ChampionRollbackResult("STALE_CURRENT_CHAMPION", current.active_entry_id, None)
            destination = session.query(ChampionRegistryEntry).filter_by(
                id=destination_champion_id, company_id=company_id, material_code=material_code, demand_type=demand_type
            ).one_or_none()
            if destination is None or destination.id == current.active_entry_id:
                return ChampionRollbackResult("INVALID_DESTINATION", current.active_entry_id, None)
            if destination.entry_type == "xgboost_artifact":
                try:
                    artifacts = self._artifact_service_factory(session) if self._artifact_service_factory else XGBoostChallengerArtifactService(session)
                    artifact = artifacts.get(company_id, destination.model_artifact_id)
                    if artifact.material_code != material_code or artifact.demand_type != demand_type or artifact.model_family != "xgboost":
                        return ChampionRollbackResult("INVALID_DESTINATION", current.active_entry_id, None)
                    artifacts.load(company_id, artifact.id)
                except (LookupError, ArtifactIntegrityError, OSError, ValueError, XGBoostError):
                    return ChampionRollbackResult("INVALID_DESTINATION", current.active_entry_id, None)
            elif destination.entry_type != "classical_existing":
                return ChampionRollbackResult("INVALID_DESTINATION", current.active_entry_id, None)
            transition = ChampionRegistryTransition(
                company_id=company_id, material_code=material_code, demand_type=demand_type, transition_type="ROLLBACK",
                source_entry_id=current.active_entry_id, destination_entry_id=destination.id,
                source_decision_id=None, expected_current_entry_id=expected_current_champion_id,
                reason=reason.strip(), idempotency_fingerprint=fingerprint,
            )
            session.add(transition)
            current.active_entry_id = destination.id
            current.row_version += 1
            session.commit()
            return ChampionRollbackResult("ROLLED_BACK", destination.id, transition.id)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
