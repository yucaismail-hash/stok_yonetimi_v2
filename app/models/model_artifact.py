"""Immutable, tenant-scoped metadata for persisted Challenger model binaries."""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class ModelArtifact(BaseModel):
    __tablename__ = "model_artifacts"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    model_role = Column(String(32), nullable=False, default="challenger")
    model_family = Column(String(32), nullable=False, default="xgboost")
    model_version = Column(String(32), nullable=False)
    artifact_contract_version = Column(String(32), nullable=False)
    xgboost_version = Column(String(32), nullable=False)
    feature_schema_version = Column(String(64), nullable=False)
    encoding_contract_version = Column(String(64), nullable=False)
    split_policy_version = Column(String(64), nullable=False)
    training_cutoff_period = Column(String(8), nullable=False)
    training_period_start = Column(String(8), nullable=False)
    training_period_end = Column(String(8), nullable=False)
    validation_period_start = Column(String(8), nullable=False)
    validation_period_end = Column(String(8), nullable=False)
    training_sample_count = Column(Integer, nullable=False)
    validation_sample_count = Column(Integer, nullable=False)
    seed = Column(Integer, nullable=False)
    model_parameters = Column(JSONB, nullable=False)
    validation_wape = Column(Numeric(18, 10), nullable=True)
    validation_bias = Column(Numeric(18, 10), nullable=True)
    validation_mae = Column(Numeric(18, 10), nullable=True)
    validation_rmse = Column(Numeric(18, 10), nullable=True)
    artifact_storage_reference = Column(String(512), nullable=False, unique=True)
    artifact_checksum = Column(String(64), nullable=False)
    artifact_size_bytes = Column(BigInteger, nullable=False)
    source_actual_observation_ids = Column(JSONB, nullable=False)
    source_evidence_signature = Column(String(64), nullable=False)
    eligibility_evidence = Column(JSONB, nullable=True)
    source_evaluation_ids = Column(JSONB, nullable=True)
    artifact_fingerprint = Column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "artifact_fingerprint", name="uq_model_artifact_company_fingerprint"),
    )


@event.listens_for(ModelArtifact, "before_update")
def _forbid_model_artifact_update(mapper, connection, target):
    raise ValueError("ModelArtifact is immutable")
