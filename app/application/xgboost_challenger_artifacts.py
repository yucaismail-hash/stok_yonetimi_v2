"""Explicit persistence and trusted loading for immutable Challenger model artifacts."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import xgboost
from sqlalchemy.exc import IntegrityError
from uuid_extensions import uuid7

from app.application.xgboost_challenger_training import XGBoostChallengerTrainingRequest
from app.application.xgboost_weekly_features import FEATURE_SCHEMA_VERSION
from app.models.model_artifact import ModelArtifact
from app.services.model_artifact_storage import LocalModelArtifactStorage


MODEL_ARTIFACT_CONTRACT_VERSION = "1.0.0"


class ArtifactIntegrityError(RuntimeError):
    """Raised before deserialization when trusted artifact verification fails."""


@dataclass(frozen=True)
class PersistedChallengerArtifact:
    artifact: ModelArtifact
    created: bool


class XGBoostChallengerArtifactService:
    """Persists only successful bounded Challenger runs; never promotes or selects models."""

    def __init__(self, session, storage=None):
        self.session = session
        self.storage = storage or LocalModelArtifactStorage()

    def persist(self, request: XGBoostChallengerTrainingRequest, result) -> PersistedChallengerArtifact:
        if result.status != "TRAINED" or result.model is None or result.metrics is None:
            raise ValueError("only a successfully trained Challenger may be persisted")
        fingerprint = self._fingerprint(request, result)
        existing = self.session.query(ModelArtifact).filter_by(
            company_id=request.company_id, artifact_fingerprint=fingerprint
        ).one_or_none()
        if existing is not None:
            return PersistedChallengerArtifact(existing, False)

        artifact_id = uuid7()
        payload = bytes(result.model.get_booster().save_raw(raw_format="ubj"))
        checksum = hashlib.sha256(payload).hexdigest()
        reference = self.storage.write(request.company_id, artifact_id, payload)
        try:
            artifact = ModelArtifact(
                id=artifact_id,
                company_id=request.company_id,
                material_code=request.material_code,
                demand_type=request.demand_type,
                model_role="challenger",
                model_family="xgboost",
                model_version=result.contract_version,
                artifact_contract_version=MODEL_ARTIFACT_CONTRACT_VERSION,
                xgboost_version=result.xgboost_version,
                feature_schema_version=result.feature_schema_version,
                encoding_contract_version=result.categorical_encoding_version,
                split_policy_version=result.split_policy_version,
                training_cutoff_period=request.training_cutoff_period,
                training_period_start=result.training_target_periods[0],
                training_period_end=result.training_target_periods[-1],
                validation_period_start=result.validation_target_periods[0],
                validation_period_end=result.validation_target_periods[-1],
                training_sample_count=result.training_count,
                validation_sample_count=result.validation_count,
                seed=result.seed,
                model_parameters=result.parameters,
                validation_wape=result.metrics.wape,
                validation_bias=result.metrics.bias,
                validation_mae=result.metrics.mae,
                validation_rmse=result.metrics.rmse,
                artifact_storage_reference=reference,
                artifact_checksum=checksum,
                artifact_size_bytes=len(payload),
                source_actual_observation_ids=list(result.source_actual_observation_ids),
                source_evidence_signature=result.source_evidence_signature,
                eligibility_evidence=self._eligibility_evidence(request.eligibility_evidence),
                source_evaluation_ids=self._source_evaluation_ids(request.eligibility_evidence),
                artifact_fingerprint=fingerprint,
            )
            # The PostgreSQL fingerprint constraint is authoritative across workers.
            # A savepoint preserves the caller's training/task transaction when a
            # competing worker wins the insert race.
            try:
                with self.session.begin_nested():
                    self.session.add(artifact)
                    self.session.flush()
            except IntegrityError:
                self.storage.delete_for_controlled_cleanup(reference)
                existing = self.session.query(ModelArtifact).filter_by(
                    company_id=request.company_id, artifact_fingerprint=fingerprint
                ).one_or_none()
                if existing is not None:
                    return PersistedChallengerArtifact(existing, False)
                raise
            return PersistedChallengerArtifact(artifact, True)
        except Exception:
            self.storage.delete_for_controlled_cleanup(reference)
            raise

    def get(self, company_id, artifact_id) -> ModelArtifact:
        artifact = self.session.query(ModelArtifact).filter_by(
            id=artifact_id, company_id=company_id
        ).one_or_none()
        if artifact is None:
            raise LookupError("MODEL_ARTIFACT_NOT_FOUND")
        return artifact

    def load(self, company_id, artifact_id):
        artifact = self.get(company_id, artifact_id)
        if artifact.feature_schema_version != FEATURE_SCHEMA_VERSION:
            raise ArtifactIntegrityError("ARTIFACT_FEATURE_SCHEMA_INCOMPATIBLE")
        if artifact.xgboost_version != xgboost.__version__:
            raise ArtifactIntegrityError("ARTIFACT_XGBOOST_VERSION_INCOMPATIBLE")
        payload = self.storage.read(artifact.artifact_storage_reference)
        if len(payload) != artifact.artifact_size_bytes or hashlib.sha256(payload).hexdigest() != artifact.artifact_checksum:
            raise ArtifactIntegrityError("ARTIFACT_INTEGRITY_ERROR")
        model = xgboost.XGBRegressor()
        model.load_model(bytearray(payload))
        return model

    @staticmethod
    def _fingerprint(request, result) -> str:
        payload = {
            "company_id": str(request.company_id),
            "material_code": request.material_code,
            "demand_type": request.demand_type,
            "training_cutoff_period": request.training_cutoff_period,
            "feature_schema_version": result.feature_schema_version,
            "split_policy_version": result.split_policy_version,
            "encoding_contract_version": result.categorical_encoding_version,
            "parameters": result.parameters,
            "seed": result.seed,
            "source_evidence_signature": result.source_evidence_signature,
            "retraining_candidate_fingerprint": (
                request.eligibility_evidence.get("candidate_fingerprint")
                if isinstance(request.eligibility_evidence, dict) else None
            ),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _eligibility_evidence(evidence: Any | None):
        if evidence is None:
            return None
        if isinstance(evidence, dict):
            return evidence
        return {"tier": getattr(evidence, "tier", None), "reason_codes": list(getattr(evidence, "reason_codes", ())) }

    @staticmethod
    def _source_evaluation_ids(evidence: Any | None):
        if isinstance(evidence, dict):
            values = evidence.get("evaluation_ids") or ([] if evidence.get("latest_evaluation_id") is None else [evidence["latest_evaluation_id"]])
            return [str(value) for value in values] or None
        latest = getattr(evidence, "latest_evaluation_id", None) if evidence is not None else None
        return [str(latest)] if latest is not None else None
