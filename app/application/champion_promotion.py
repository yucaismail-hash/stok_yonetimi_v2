"""Explicit controlled promotion; it changes registry state only."""
import hashlib
from dataclasses import dataclass

from app.application.champion_challenger_evaluation import POLICY_VERSION
from app.application.xgboost_challenger_artifacts import XGBoostChallengerArtifactService
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition


@dataclass(frozen=True)
class ChampionPromotionResult:
    status: str
    active_entry_id: object | None
    transition_id: object | None


class ChampionPromotionService:
    def __init__(self, session_factory=SessionLocal, artifact_service_factory=None):
        self._session_factory = session_factory; self._artifact_service_factory = artifact_service_factory

    def promote(self, company_id, decision_id, expected_current_entry_id=None, expected_row_version=None):
        session = self._session_factory()
        try:
            decision = session.query(ChampionChallengerDecision).filter_by(id=decision_id, company_id=company_id).one_or_none()
            if decision is None: return ChampionPromotionResult("DECISION_NOT_FOUND", None, None)
            if decision.decision != "PROMOTE_CHALLENGER" or decision.policy_version != POLICY_VERSION:
                return ChampionPromotionResult("NOT_PROMOTABLE", None, None)
            artifacts = self._artifact_service_factory(session) if self._artifact_service_factory else XGBoostChallengerArtifactService(session)
            artifact = artifacts.get(company_id, decision.challenger_model_artifact_id)
            if artifact.material_code != decision.material_code or artifact.demand_type != decision.demand_type or artifact.model_role != "challenger" or artifact.model_family != "xgboost":
                return ChampionPromotionResult("ARTIFACT_SCOPE_MISMATCH", None, None)
            artifacts.load(company_id, artifact.id)
            existing = session.query(ChampionRegistryTransition).filter_by(company_id=company_id, source_decision_id=decision.id, transition_type="PROMOTION").one_or_none()
            if existing is not None:
                return ChampionPromotionResult("ALREADY_PROMOTED", existing.destination_entry_id, existing.id)
            current = session.query(ChampionRegistryCurrent).filter_by(company_id=company_id, material_code=decision.material_code, demand_type=decision.demand_type).with_for_update().one_or_none()
            if current is None: return ChampionPromotionResult("REGISTRY_NOT_BOOTSTRAPPED", None, None)
            existing = session.query(ChampionRegistryTransition).filter_by(company_id=company_id, source_decision_id=decision.id, transition_type="PROMOTION").one_or_none()
            if existing is not None:
                return ChampionPromotionResult("ALREADY_PROMOTED", existing.destination_entry_id, existing.id)
            if expected_current_entry_id is None or current.active_entry_id != expected_current_entry_id or (expected_row_version is not None and current.row_version != expected_row_version):
                return ChampionPromotionResult("STALE_DECISION", current.active_entry_id, None)
            entry = session.query(ChampionRegistryEntry).filter_by(company_id=company_id, model_artifact_id=artifact.id).one_or_none()
            if entry is None:
                metadata = decision.champion_evidence.get("product_metadata", {}) if isinstance(decision.champion_evidence, dict) else {}
                entry = ChampionRegistryEntry(company_id=company_id, material_code=artifact.material_code, demand_type=artifact.demand_type, entry_type="xgboost_artifact", model_artifact_id=artifact.id, product_level=metadata.get("product_level"), product_group=metadata.get("product_group"), product_class=metadata.get("product_class"), provenance={"artifact_checksum": artifact.artifact_checksum, "feature_schema_version": artifact.feature_schema_version, "xgboost_version": artifact.xgboost_version, "training_cutoff_period": artifact.training_cutoff_period})
                session.add(entry); session.flush()
            fingerprint = hashlib.sha256(f"{company_id}:{decision.id}:PROMOTION".encode()).hexdigest()
            transition = ChampionRegistryTransition(company_id=company_id, material_code=decision.material_code, demand_type=decision.demand_type, transition_type="PROMOTION", source_entry_id=current.active_entry_id, destination_entry_id=entry.id, source_decision_id=decision.id, expected_current_entry_id=expected_current_entry_id, reason="immutable PROMOTE_CHALLENGER decision", idempotency_fingerprint=fingerprint)
            session.add(transition); current.active_entry_id = entry.id; current.row_version += 1; session.commit()
            return ChampionPromotionResult("PROMOTED", entry.id, transition.id)
        except Exception:
            session.rollback(); raise
        finally: session.close()
