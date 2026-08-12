"""Durable, tenant-scoped Champion Registry identities and history."""
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, UniqueConstraint, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.models.base import BaseModel


class ChampionRegistryEntry(BaseModel):
    __tablename__ = "champion_registry_entries"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    entry_type = Column(String(32), nullable=False)
    classical_strategy = Column(String(128), nullable=True)
    model_artifact_id = Column(PG_UUID(as_uuid=True), ForeignKey("model_artifacts.id", ondelete="RESTRICT"), nullable=True)
    product_level = Column(String(32), nullable=True)
    product_group = Column(String(128), nullable=True)
    product_class = Column(String(128), nullable=True)
    provenance = Column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint("entry_type IN ('classical_existing', 'xgboost_artifact')", name="ck_champion_entry_type"),
        CheckConstraint("(entry_type = 'classical_existing' AND classical_strategy IS NOT NULL AND model_artifact_id IS NULL) OR (entry_type = 'xgboost_artifact' AND classical_strategy IS NULL AND model_artifact_id IS NOT NULL)", name="ck_champion_entry_reference"),
    )


class ChampionRegistryCurrent(BaseModel):
    __tablename__ = "champion_registry_current"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    active_entry_id = Column(PG_UUID(as_uuid=True), ForeignKey("champion_registry_entries.id", ondelete="RESTRICT"), nullable=False)
    row_version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("company_id", "material_code", "demand_type", name="uq_champion_current_scope"),
        CheckConstraint("row_version >= 1", name="ck_champion_current_version"),
    )


class ChampionRegistryTransition(BaseModel):
    __tablename__ = "champion_registry_transitions"

    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    material_code = Column(String(128), nullable=False)
    demand_type = Column(String(16), nullable=False)
    transition_type = Column(String(16), nullable=False)
    source_entry_id = Column(PG_UUID(as_uuid=True), ForeignKey("champion_registry_entries.id", ondelete="RESTRICT"), nullable=True)
    destination_entry_id = Column(PG_UUID(as_uuid=True), ForeignKey("champion_registry_entries.id", ondelete="RESTRICT"), nullable=False)
    source_decision_id = Column(PG_UUID(as_uuid=True), ForeignKey("champion_challenger_decisions.id", ondelete="RESTRICT"), nullable=True)
    expected_current_entry_id = Column(PG_UUID(as_uuid=True), ForeignKey("champion_registry_entries.id", ondelete="RESTRICT"), nullable=True)
    reason = Column(String(256), nullable=False)
    idempotency_fingerprint = Column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "idempotency_fingerprint", name="uq_champion_transition_fingerprint"),
        CheckConstraint("transition_type IN ('BOOTSTRAP', 'PROMOTION', 'ROLLBACK')", name="ck_champion_transition_type"),
    )


def _immutable(mapper, connection, target):
    raise ValueError(f"{type(target).__name__} is immutable")


event.listen(ChampionRegistryEntry, "before_update", _immutable)
event.listen(ChampionRegistryTransition, "before_update", _immutable)
