"""PostgreSQL proof for immutable, tenant-scoped Challenger model artifacts."""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uuid_extensions import uuid7

from app.analysis.forecast import DemandForecaster
from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.application.xgboost_challenger_artifacts import (
    ArtifactIntegrityError,
    XGBoostChallengerArtifactService,
)
from app.application.xgboost_challenger_training import (
    XGBoostChallengerTrainingRequest,
    XGBoostChallengerTrainingService,
)
from app.application.xgboost_weekly_features import XGBoostWeeklyFeatureBuilder
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.forecast_vintage import ForecastVintage
from app.models.model_artifact import ModelArtifact
from app.models.runtime import RuntimeResultReference, RuntimeTaskAttempt
from app.models.security import CompanyEncryptionKey
from app.services.model_artifact_storage import LocalModelArtifactStorage
from app.services.security import EncryptionService


def _row(week, quantity):
    return {
        "material_code": "SKU",
        "period": f"2026-W{week:02d}",
        "quantity": quantity,
        "product_level": "finished_good",
        "product_group": "G",
        "product_class": "C",
    }


def _request(company_id, cutoff, evidence=None):
    return XGBoostChallengerTrainingRequest(
        company_id=company_id,
        material_code="SKU",
        demand_type="sales",
        training_cutoff_period=cutoff,
        eligibility_evidence=evidence,
        seed=23,
    )


def _counts(session, company_id):
    return {
        "actuals": session.query(ActualWeeklyObservation).filter_by(company_id=company_id).count(),
        "revisions": session.query(ActualWeeklyRevision).filter_by(company_id=company_id).count(),
        "vintages": session.query(ForecastVintage).filter_by(company_id=company_id).count(),
        "evaluations": session.query(ForecastEvaluation).filter_by(company_id=company_id).count(),
        "runtime_results": session.query(RuntimeResultReference).filter_by(company_id=company_id).count(),
        "runtime_attempts": session.query(RuntimeTaskAttempt).filter_by(company_id=company_id).count(),
        "artifacts": session.query(ModelArtifact).filter_by(company_id=company_id).count(),
    }


def main() -> None:
    session = SessionLocal()
    company_id = user_id = other_company_id = other_user_id = None
    storage = LocalModelArtifactStorage(Path(__file__).resolve().parents[1] / ".phase3c2b3_probe_artifacts")
    references = []
    try:
        token = "phase3c2b3_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=token, tax_id=token)
        user = User(id=uuid7(), company_id=company.id, email=f"{token}@x.invalid", hashed_password="x")
        other_company = Company(id=uuid7(), name=token + "_other", tax_id=token + "_other")
        other_user = User(id=uuid7(), company_id=other_company.id, email=f"{token}_other@x.invalid", hashed_password="x")
        session.add_all((company, user, other_company, other_user))
        session.flush()
        company_id, user_id = company.id, user.id
        other_company_id, other_user_id = other_company.id, other_user.id
        dataset = Dataset(
            id=uuid7(), company_id=company_id, user_id=user_id, uploaded_by=user_id,
            dataset_hash=hashlib.sha256(token.encode()).hexdigest(), source_type=token,
            encrypted_data=EncryptionService(session).encrypt_dataset(user_id, {"items": []}),
            is_active=True,
        )
        session.add(dataset)
        session.commit()

        ledger = ActualWeeklyLedgerService()
        ledger.ingest_dataset_actuals(company_id, user_id, dataset.id, [_row(week, 100 + week) for week in range(1, 21)], "sales")
        session.close()
        session = SessionLocal()
        trainer = XGBoostChallengerTrainingService(session)
        artifacts = XGBoostChallengerArtifactService(session, storage)

        import xgboost

        fit_calls = {"challenger": 0, "forecast": 0}
        original_fit, original_forecast = xgboost.XGBRegressor.fit, DemandForecaster.forecast

        def counted_fit(model, *args, **kwargs):
            fit_calls["challenger"] += 1
            return original_fit(model, *args, **kwargs)

        def counted_forecast(model, *args, **kwargs):
            fit_calls["forecast"] += 1
            return original_forecast(model, *args, **kwargs)

        xgboost.XGBRegressor.fit, DemandForecaster.forecast = counted_fit, counted_forecast
        try:
            evidence = {"tier": "TIER_3_DEEP_LEARN_RETRAIN", "evaluation_ids": ["fixture-evaluation"]}
            request_a = _request(company_id, "2026-W20", evidence)
            trained_a = trainer.train(request_a)
            assert trained_a.status == "TRAINED"
            persisted_a = artifacts.persist(request_a, trained_a)
            session.commit()
            artifact_a = persisted_a.artifact
            references.append(artifact_a.artifact_storage_reference)
            assert persisted_a.created and storage.exists(artifact_a.artifact_storage_reference)
            assert hashlib.sha256(storage.read(artifact_a.artifact_storage_reference)).hexdigest() == artifact_a.artifact_checksum
            assert artifact_a.artifact_size_bytes == len(storage.read(artifact_a.artifact_storage_reference))
            assert artifact_a.source_evaluation_ids == ["fixture-evaluation"]

            duplicate = artifacts.persist(request_a, trained_a)
            assert not duplicate.created and duplicate.artifact.id == artifact_a.id
            builder = XGBoostWeeklyFeatureBuilder(session)
            matrix_a = builder.build(company_id, "SKU", "sales", "2026-W20")
            validation_x = trainer._encoded_rows(matrix_a)[-trained_a.validation_count:]
            original_predictions = trained_a.model.predict(validation_x)
            loaded_predictions = artifacts.load(company_id, artifact_a.id).predict(validation_x)
            assert tuple(float(value) for value in original_predictions) == tuple(float(value) for value in loaded_predictions)

            immutable_snapshot = (artifact_a.training_cutoff_period, artifact_a.artifact_checksum, artifact_a.model_parameters)
            ledger.ingest_dataset_actuals(company_id, user_id, dataset.id, [_row(week, 100 + week) for week in range(21, 25)], "sales")
            request_b = _request(company_id, "2026-W24")
            trained_b = trainer.train(request_b)
            persisted_b = artifacts.persist(request_b, trained_b)
            session.commit()
            artifact_b = persisted_b.artifact
            references.append(artifact_b.artifact_storage_reference)
            assert persisted_b.created and artifact_a.id != artifact_b.id
            session.refresh(artifact_a)
            assert immutable_snapshot == (artifact_a.training_cutoff_period, artifact_a.artifact_checksum, artifact_a.model_parameters)
            try:
                artifact_a.seed = 99
                session.flush()
                raise AssertionError("immutable artifact accepted an update")
            except ValueError as exc:
                assert str(exc) == "ModelArtifact is immutable"
                session.rollback()

            try:
                artifacts.get(other_company_id, artifact_a.id)
                raise AssertionError("cross-tenant metadata retrieval was allowed")
            except LookupError as exc:
                assert str(exc) == "MODEL_ARTIFACT_NOT_FOUND"
            try:
                artifacts.load(other_company_id, artifact_a.id)
                raise AssertionError("cross-tenant artifact load was allowed")
            except LookupError as exc:
                assert str(exc) == "MODEL_ARTIFACT_NOT_FOUND"

            # Controlled probe-only corruption: load must fail before deserialization.
            (storage.base_directory / artifact_b.artifact_storage_reference).write_bytes(b"corrupt")
            try:
                artifacts.load(company_id, artifact_b.id)
                raise AssertionError("corrupt artifact loaded")
            except ArtifactIntegrityError as exc:
                assert str(exc) == "ARTIFACT_INTEGRITY_ERROR"

            short_request = _request(company_id, "2026-W08")
            not_trainable = trainer.train(short_request)
            not_eligible = trainer.train(_request(company_id, "2026-W20", {"tier": "TIER_1_EVALUATE"}))
            artifact_count = _counts(session, company_id)["artifacts"]
            for result in (not_trainable, not_eligible):
                try:
                    artifacts.persist(short_request, result)
                    raise AssertionError("untrained Challenger persisted")
                except ValueError:
                    pass
            assert _counts(session, company_id)["artifacts"] == artifact_count
            assert fit_calls == {"challenger": 2, "forecast": 0}
            assert _counts(session, company_id)["vintages"] == 0
            assert _counts(session, company_id)["evaluations"] == 0
        finally:
            xgboost.XGBRegressor.fit, DemandForecaster.forecast = original_fit, original_forecast

        print("PHASE3C2B3 PASS", {"xgboost": xgboost.__version__, "artifacts": 2, "challenger_fit_calls": fit_calls["challenger"]})
    finally:
        if company_id:
            for reference in references:
                storage.delete_for_controlled_cleanup(reference)
            session.query(ModelArtifact).filter_by(company_id=company_id).delete(synchronize_session=False)
            session.query(ActualWeeklyRevision).filter_by(company_id=company_id).delete(synchronize_session=False)
            session.query(ActualWeeklyObservation).filter_by(company_id=company_id).delete(synchronize_session=False)
            session.query(Dataset).filter_by(company_id=company_id).delete(synchronize_session=False)
            session.query(CompanyEncryptionKey).filter(CompanyEncryptionKey.user_id.in_((user_id, other_user_id))).delete(synchronize_session=False)
            session.query(User).filter(User.id.in_((user_id, other_user_id))).delete(synchronize_session=False)
            session.query(Company).filter(Company.id.in_((company_id, other_company_id))).delete(synchronize_session=False)
            session.commit()
            assert session.query(ModelArtifact).filter_by(company_id=company_id).count() == 0
            assert session.query(Company).filter(Company.id.in_((company_id, other_company_id))).count() == 0
        session.close()


if __name__ == "__main__":
    main()
