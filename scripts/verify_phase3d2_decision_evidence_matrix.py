"""Focused persisted PostgreSQL matrix for ``DecisionEvidenceResolver``.

This deliberately creates compact durable projections, not analytical output
fixtures.  The resolver owns no writes; every assertion below reloads the
same database-backed evidence it is intended to normalize.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.application.decision_evidence_resolver import DecisionEvidenceResolver
from app.database import SessionLocal
from app.models.champion_challenger_decision import ChampionChallengerDecision
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company, User, Supplier
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.dataset import Dataset
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.model_artifact import ModelArtifact
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution, RuntimeResultReference
from app.models.security import CompanyEncryptionKey
from app.models.supplier_learning_memory import SupplierLearningMemory
from app.services.model_artifact_storage import LocalModelArtifactStorage
from app.services.security import EncryptionService

T1 = "2026-W20"
T2 = "2026-W24"


def _context(tag):
    s = SessionLocal()
    try:
        company = Company(id=uuid7(), name=tag, tax_id=tag)
        user = User(id=uuid7(), company_id=company.id, email=tag + "@invalid.test", hashed_password="x")
        s.add_all((company, user)); s.flush()
        dataset = Dataset(
            id=uuid7(), company_id=company.id, user_id=user.id, uploaded_by=user.id,
            dataset_hash=sha256(tag.encode()).hexdigest(), source_type="phase3d2_matrix",
            encrypted_data=EncryptionService(s).encrypt_dataset(user.id, {"items": []}), is_active=True,
        )
        s.add(dataset); s.commit()
        return {"company_id": company.id, "user_id": user.id, "dataset_id": dataset.id}
    finally:
        s.close()


def _execution(s, ids, material, demand, cutoff, kind):
    execution = RuntimeExecution(
        execution_id=uuid7(), company_id=ids["company_id"], user_id=ids["user_id"], dataset_id=ids["dataset_id"],
        workflow_id="phase3d2-matrix", analysis_type=kind, state="completed",
        metadata_={"params": {"analysis_cutoff_period": cutoff, "demand_type": demand,
                               "forecast_vintage": {"input_cutoff_period": cutoff, "demand_type": demand}}},
    )
    s.add(execution); s.flush()
    return execution


def _runtime(s, ids, material, demand, cutoff, kind):
    execution = _execution(s, ids, material, demand, cutoff, kind)
    reference = RuntimeResultReference(
        id=uuid7(), company_id=ids["company_id"], execution_id=execution.execution_id,
        result_type=kind, result_version="phase3d2-v1", contract_version="1", storage_kind="inline_jsonb",
        inline_result={"items": [{"material_code": material, "demand_type": demand}]}, validation_status="validated",
    )
    s.add(reference); s.flush()
    return execution, reference


def _forecast(s, ids, material, demand, cutoff, level):
    execution, reference = _runtime(s, ids, material, demand, cutoff, "forecast")
    vintage = ForecastVintage(
        company_id=ids["company_id"], execution_id=execution.execution_id, runtime_result_reference_id=reference.id,
        dataset_id=ids["dataset_id"], forecast_available_at=datetime.now(timezone.utc),
        forecast_origin_period=cutoff, input_cutoff_period=cutoff, demand_type=demand,
        result_version="phase3d2-v1", contract_version="1",
    )
    s.add(vintage); s.flush()
    s.add(ForecastVintagePoint(forecast_vintage_id=vintage.id, material_code=material, target_period="2026-W21",
                               forecast_value=Decimal("100"), product_level=level, horizon_index=1))
    s.flush()
    return reference, vintage


def _pattern(ids, material, demand, cutoff, fingerprint):
    return PatternLearningMemory(
        company_id=ids["company_id"], material_code=material, demand_type=demand, product_level="finished_good",
        pattern_classification="stable", pattern_policy_version="p1", feature_version="f1", confidence_policy_version="c1",
        sample_count=12, period_start="2026-W09", period_end=cutoff, cutoff_period=cutoff,
        coverage_ratio=Decimal("1"), missing_period_count=0, mean_demand=Decimal("100"), std_demand=Decimal("1"),
        coefficient_of_variation=Decimal(".01"), zero_demand_ratio=Decimal("0"), seasonality_status="insufficient",
        confidence=Decimal(".9"), source_pattern_fingerprint=fingerprint, source_learning_evidence_ids=[], row_version=1,
    )


def _event(ids, identity, cutoff):
    return EventIntelligenceMemory(
        company_id=ids["company_id"], material_code="MAT-A", demand_type="sales", event_identity=identity,
        feature_schema_version="v1", baseline_policy_version="v1", lag_policy_version="v1", association_policy_version="v1",
        confidence_policy_version="v1", classification="POSITIVE", confidence=Decimal(".8"), occurrence_count=2,
        included_occurrence_ids=[], included_revision_ids=[], cutoff_period=cutoff, source_fingerprint=sha256(identity.encode()).hexdigest(),
        source_actual_observation_ids=[], source_actual_revision_ids=[], source_scope_metadata={}, overlap_confounded=False,
    )


def _supplier_memory(ids, supplier):
    return SupplierLearningMemory(
        company_id=ids["company_id"], supplier_id=supplier.id, material_code="MAT-A", supplier_code="SUP-A", supplier_name="Supplier A",
        product_level="finished_good", supplier_learning_policy_version="v1", feature_version="v1", confidence_policy_version="v1",
        classification="RELIABLE", confidence=Decimal(".9"), sample_count=8, lead_time_sample_count=8,
        window_start=date(2026, 1, 1), window_end=date(2026, 5, 17), cutoff_date=date(2026, 5, 17),
        promised_delivery_sample_count=8, on_time_count=8, late_count=0, fulfillment_sample_count=8,
        underfulfillment_count=0, recent_window_size=4, recent_deterioration_evaluated="true", recent_deterioration_dimensions=[],
        source_fingerprint="s" * 64, source_observation_ids=[], accepted_revision_ids=[], row_version=1,
    )


def _read_only_counts(s, company_id):
    tables = (RuntimeExecution, RuntimeResultReference, ForecastVintage, PatternLearningMemory, CompanyLearningMemoryV2,
              SupplierLearningMemory, EventIntelligenceMemory, RetrainingJob, ModelArtifact, ChampionRegistryEntry,
              ChampionRegistryCurrent)
    return tuple(s.query(table).filter_by(company_id=company_id).count() for table in tables)


def _cleanup(ids, artifact_refs):
    s = SessionLocal()
    try:
        company_ids = [row["company_id"] for row in ids]
        execution_ids = [row[0] for row in s.query(RuntimeExecution.execution_id).filter(RuntimeExecution.company_id.in_(company_ids)).all()]
        vintage_ids = [row[0] for row in s.query(ForecastVintage.id).filter(ForecastVintage.company_id.in_(company_ids)).all()]
        s.query(RetrainingJob).filter(RetrainingJob.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(ForecastEvaluation).filter(ForecastEvaluation.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(ForecastVintagePoint).filter(ForecastVintagePoint.forecast_vintage_id.in_(vintage_ids)).delete(synchronize_session=False)
        s.query(ForecastVintage).filter(ForecastVintage.id.in_(vintage_ids)).delete(synchronize_session=False)
        s.query(EventIntelligenceMemory).filter(EventIntelligenceMemory.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(SupplierLearningMemory).filter(SupplierLearningMemory.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(PatternLearningMemory).filter(PatternLearningMemory.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(CompanyLearningMemoryV2).filter(CompanyLearningMemoryV2.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(RuntimeResultReference).filter(RuntimeResultReference.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        s.query(RuntimeExecution).filter(RuntimeExecution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
        s.query(ChampionRegistryCurrent).filter(ChampionRegistryCurrent.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(ChampionRegistryTransition).filter(ChampionRegistryTransition.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(ChampionRegistryEntry).filter(ChampionRegistryEntry.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(ChampionChallengerDecision).filter(ChampionChallengerDecision.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(ModelArtifact).filter(ModelArtifact.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(Supplier).filter(Supplier.company_id.in_(company_ids)).delete(synchronize_session=False)
        for ref in artifact_refs:
            LocalModelArtifactStorage().delete_for_controlled_cleanup(ref)
        s.query(Dataset).filter(Dataset.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(CompanyEncryptionKey).filter(CompanyEncryptionKey.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(User).filter(User.company_id.in_(company_ids)).delete(synchronize_session=False)
        s.query(Company).filter(Company.id.in_(company_ids)).delete(synchronize_session=False)
        s.commit()
        assert s.query(Company).filter(Company.id.in_(company_ids)).count() == 0
    finally:
        s.close()


def main():
    primary = neighbor_material = neighbor_demand = tenant = no_supplier = None
    refs = []
    try:
        tag = "phase3d2_matrix_" + str(uuid7())
        primary, neighbor_material, neighbor_demand, tenant, no_supplier = (_context(tag + suffix) for suffix in ("_a", "_material", "_demand", "_tenant", "_no_supplier"))
        s = SessionLocal()
        try:
            forecast_ref, vintage = _forecast(s, primary, "MAT-A", "sales", T1, "finished_good")
            forecast_reference_id, vintage_id = forecast_ref.id, vintage.id
            runtime_t1 = {kind: _runtime(s, primary, "MAT-A", "sales", T1, kind)[1] for kind in ("safety_stock", "supplier", "simulation", "backtest")}
            runtime_t1_ids = {kind: reference.id for kind, reference in runtime_t1.items()}
            # Neighboring material/demand/tenant records intentionally use the same cutoff.
            _forecast(s, neighbor_material, "MAT-B", "sales", T1, "finished_good")
            _forecast(s, neighbor_demand, "MAT-A", "consumption", T1, "finished_good")
            _forecast(s, tenant, "MAT-A", "sales", T1, "finished_good")
            _forecast(s, no_supplier, "MAT-NO-SUPPLIER", "sales", T1, "finished_good")
            s.add(_pattern(primary, "MAT-A", "sales", T1, "p" * 64))
            s.add(_pattern(primary, "MAT-A", "consumption", T1, "c" * 64))
            s.add(CompanyLearningMemoryV2(company_id=primary["company_id"], company_learning_policy_version="v1", learning_score_policy_version="v1",
                evidence_count=10, evidence_type_counts={}, evidence_source_diversity=2, material_scope_count=1, demand_scope_count=1,
                pattern_memory_scope_count=1, forecast_evaluated_scope_count=1, forecast_evaluation_sample_count=5,
                pattern_distribution={}, accepted_correction_evidence_count=0, retraining_summary={}, champion_summary={},
                evidence_maturity_score=Decimal("70"), evidence_maturity_level="mature", source_summary_fingerprint="m" * 64, row_version=1))
            supplier = Supplier(id=uuid7(), company_id=primary["company_id"], code="SUP-A", name="Supplier A")
            s.add(supplier); s.flush(); s.add(_supplier_memory(primary, supplier))
            s.add_all((_event(primary, "EVENT_A", T1), _event(primary, "EVENT_B", T1), _event(primary, "EVENT_FUTURE", T2)))
            # Uses the verified artifact/registry bootstrap and promotion boundary; no inference or fit.
            from scripts.verify_phase3c3b3b1_scope_r6_closeout import _artifact
            artifact_id = _artifact(s, primary["company_id"], "MAT-A", "sales", "finished_good", refs)
            evaluation = ForecastEvaluation(company_id=primary["company_id"], demand_type="sales", start_period="2026-W16", end_period=T1,
                metric_contract_version="v1", evaluated_point_count=5, total_signed_error=0)
            s.add(evaluation); s.flush()
            s.add(RetrainingJob(company_id=primary["company_id"], material_code="MAT-A", demand_type="sales", state="trained",
                model_artifact_id=artifact_id, eligibility_tier="TIER_3", eligibility_action="DEEP_LEARN_RETRAIN",
                eligibility_contract_version="v1", eligibility_reason_codes=[], performance_drift=True, demand_drift=False,
                sample_count=5, evaluated_period_count=5, evaluation_start_period="2026-W16", evaluation_end_period=T1,
                latest_evaluation_id=evaluation.id, training_cutoff_period=T1, product_level="finished_good",
                evaluation_evidence_fingerprint="e" * 64, candidate_fingerprint="r" * 64, eligibility_evidence={}))
            s.commit()
            before = _read_only_counts(s, primary["company_id"])
        finally:
            s.close()

        resolver = DecisionEvidenceResolver()
        envelope = resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "REPLENISHMENT")
        repeat = resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "REPLENISHMENT")
        assert envelope.status == "READY" and envelope == repeat
        required, optional = dict(envelope.required), dict(envelope.optional)
        assert required["forecast"]["source_id"] == str(vintage_id) and required["safety_stock"]["source_id"] == str(runtime_t1_ids["safety_stock"])
        assert all(optional[name]["status"] == "AVAILABLE" for name in ("supplier_operational", "simulation", "backtest", "pattern", "company_learning", "supplier_learning", "champion", "retraining"))
        assert [row["event_identity"] for row in optional["event"]["entries"]] == ["EVENT_A", "EVENT_B"]
        assert optional["champion"]["model_artifact_id"] == str(artifact_id) and optional["champion"]["artifact_checksum"]
        assert resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "FORECAST_REVIEW").status == "READY"
        assert resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "SAFETY_STOCK").status == "READY"
        assert resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "SUPPLIER_REVIEW").status == "READY"
        assert resolver.resolve(primary["company_id"], "MAT-A", "consumption", T1, "REPLENISHMENT").status == "INSUFFICIENT_REQUIRED_EVIDENCE"
        assert resolver.resolve(neighbor_material["company_id"], "MAT-A", "sales", T1, "FORECAST_REVIEW").status == "INSUFFICIENT_REQUIRED_EVIDENCE"
        assert resolver.resolve(tenant["company_id"], "MAT-A", "sales", T1, "FORECAST_REVIEW").status == "READY"
        # A real standalone Forecast remains valid, but Replenishment/Safety
        # Stock contexts correctly reject the missing required runtime source.
        absent_replenishment = resolver.resolve(no_supplier["company_id"], "MAT-NO-SUPPLIER", "sales", T1, "REPLENISHMENT")
        absent_safety = resolver.resolve(no_supplier["company_id"], "MAT-NO-SUPPLIER", "sales", T1, "SAFETY_STOCK")
        absent_forecast = resolver.resolve(no_supplier["company_id"], "MAT-NO-SUPPLIER", "sales", T1, "FORECAST_REVIEW")
        assert absent_replenishment.status == absent_safety.status == "INSUFFICIENT_REQUIRED_EVIDENCE"
        assert dict(absent_replenishment.required)["forecast"]["status"] == "AVAILABLE"
        assert dict(absent_replenishment.required)["safety_stock"]["status"] == "ABSENT"
        assert absent_forecast.status == "READY" and dict(absent_forecast.optional)["supplier_operational"]["status"] == "ABSENT"
        # PatternLearningMemory is a single current projection.  A current
        # projection newer than the requested cutoff is retained as explicit
        # incompatible evidence and is never consumed as historical Pattern.
        s = SessionLocal()
        try:
            s.add(_pattern(no_supplier, "MAT-NO-SUPPLIER", "sales", T2, "f" * 64)); s.commit()
        finally:
            s.close()
        future_pattern = resolver.resolve(no_supplier["company_id"], "MAT-NO-SUPPLIER", "sales", T1, "FORECAST_REVIEW")
        pattern_state = dict(future_pattern.optional)["pattern"]
        assert future_pattern.status == "READY" and pattern_state["status"] == "INCOMPATIBLE" and pattern_state["reason"] == "FUTURE_EVIDENCE"
        # A later scoped runtime reference must not displace the compatible historical source.
        s = SessionLocal()
        try:
            for kind in ("safety_stock", "supplier", "simulation", "backtest"):
                _runtime(s, primary, "MAT-A", "sales", T2, kind)
            _runtime(s, primary, "MAT-B", "sales", T2, "safety_stock")
            s.commit()
            before_future_resolution = _read_only_counts(s, primary["company_id"])
        finally:
            s.close()
        after_future_runtime = resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "REPLENISHMENT")
        assert after_future_runtime == envelope
        # EVENT_FUTURE was persisted from the start.  It must neither join the
        # historical event entries nor change the historical envelope.
        assert [row["event_identity"] for row in dict(after_future_runtime.optional)["event"]["entries"]] == ["EVENT_A", "EVENT_B"]
        # Add a second supplier projection whose cutoff is later than T1.
        # SupplierLearningMemory is per supplier/material, so this is a real
        # future projection without replacing the compatible one.
        s = SessionLocal()
        try:
            future_supplier = Supplier(id=uuid7(), company_id=primary["company_id"], code="SUP-FUTURE", name="Future supplier")
            s.add(future_supplier); s.flush()
            memory = _supplier_memory(primary, future_supplier)
            memory.cutoff_date = date(2026, 6, 14)
            s.add(memory); s.commit()
        finally:
            s.close()
        after_future_supplier = resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "REPLENISHMENT")
        assert after_future_supplier == envelope
        # A semantic compatible projection mutation changes the complete
        # envelope fingerprint without relying on timestamps.
        s = SessionLocal()
        try:
            pattern = s.query(PatternLearningMemory).filter_by(company_id=primary["company_id"], material_code="MAT-A", demand_type="sales").one()
            pattern.source_pattern_fingerprint = "q" * 64
            s.commit()
        finally:
            s.close()
        changed = resolver.resolve(primary["company_id"], "MAT-A", "sales", T1, "REPLENISHMENT")
        assert changed.fingerprint != envelope.fingerprint and dict(changed.optional)["pattern"]["fingerprint"] == "q" * 64
        s = SessionLocal()
        try:
            before_final_read = _read_only_counts(s, primary["company_id"])
        finally:
            s.close()
        fresh = DecisionEvidenceResolver().resolve(primary["company_id"], "MAT-A", "sales", T1, "REPLENISHMENT")
        assert fresh == changed
        s = SessionLocal()
        try:
            assert _read_only_counts(s, primary["company_id"]) == before_final_read
        finally:
            s.close()
        print("PHASE 3D2 MATRIX PASS", {"fingerprint": envelope.fingerprint, "forecast_reference_id": str(forecast_reference_id),
              "forecast_vintage_id": str(vintage_id), "artifact_id": str(artifact_id), "event_count": 2, "read_only": True}, flush=True)
    finally:
        _cleanup([item for item in (primary, neighbor_material, neighbor_demand, tenant, no_supplier) if item], refs)


if __name__ == "__main__":
    main()
