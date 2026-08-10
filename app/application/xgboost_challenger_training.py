"""Bounded, in-memory XGBoost Challenger training over cutoff-safe weekly features."""

import hashlib
import json
from dataclasses import dataclass
from math import sqrt
from typing import Any
from uuid import UUID

import xgboost

from app.application.xgboost_weekly_features import XGBoostWeeklyFeatureBuilder


CHALLENGER_TRAINING_CONTRACT_VERSION = "1.0.0"
TIME_ORDERED_SPLIT_POLICY_VERSION = "time_ordered_holdout_v1"
CATEGORICAL_ENCODING_VERSION = "explicit_category_codes_v1"
MINIMUM_MATRIX_ROWS = 12
VALIDATION_ROW_COUNT = 4

_PRODUCT_LEVEL_CODES = {
    "finished_good": 0.0,
    "semi_finished_good": 1.0,
    "raw_material": 2.0,
}
_DEMAND_TYPE_CODES = {
    "sales": 0.0,
    "shipment": 1.0,
    "order": 2.0,
    "consumption": 3.0,
    "other": 4.0,
}
_DEFAULT_PARAMETERS = {
    "objective": "reg:squarederror",
    "n_estimators": 24,
    "max_depth": 3,
    "learning_rate": 0.1,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "n_jobs": 1,
    "tree_method": "hist",
    "verbosity": 0,
}


@dataclass(frozen=True)
class XGBoostChallengerTrainingRequest:
    company_id: UUID
    material_code: str
    demand_type: str
    training_cutoff_period: str
    eligibility_evidence: Any | None = None
    training_parameters: dict[str, Any] | None = None
    seed: int = 20260810


@dataclass(frozen=True)
class ChallengerValidationPrediction:
    target_period: str
    actual: float
    predicted: float
    error: float
    absolute_error: float
    squared_error: float


@dataclass(frozen=True)
class ChallengerMetrics:
    wape: float | None
    wape_unavailable_reason: str | None
    bias: float | None
    mae: float | None
    rmse: float | None


@dataclass(frozen=True)
class XGBoostChallengerTrainingResult:
    status: str
    reason_code: str | None
    contract_version: str
    feature_schema_version: str | None
    split_policy_version: str
    categorical_encoding_version: str
    xgboost_version: str
    seed: int
    parameters: dict[str, Any]
    feature_names: tuple[str, ...]
    source_actual_observation_ids: tuple[str, ...]
    source_evidence_signature: str | None
    training_target_periods: tuple[str, ...]
    validation_target_periods: tuple[str, ...]
    training_count: int
    validation_count: int
    validation_predictions: tuple[ChallengerValidationPrediction, ...]
    metrics: ChallengerMetrics | None
    model: Any | None


class XGBoostChallengerTrainingService:
    """Explicit Challenger-only fitting; it neither persists nor promotes a model."""

    def __init__(self, session, feature_builder=None):
        self.session = session
        self.feature_builder = feature_builder or XGBoostWeeklyFeatureBuilder(session)

    def train(self, request: XGBoostChallengerTrainingRequest) -> XGBoostChallengerTrainingResult:
        authorization_tier = self._authorization_tier(request.eligibility_evidence)
        if authorization_tier is not None and authorization_tier != "TIER_3_DEEP_LEARN_RETRAIN":
            return self._not_trained(request, "NOT_ELIGIBLE")

        matrix = self.feature_builder.build(
            request.company_id,
            request.material_code,
            request.demand_type,
            request.training_cutoff_period,
        )
        if len(matrix.X) < MINIMUM_MATRIX_ROWS:
            return self._not_trained(
                request,
                "INSUFFICIENT_TRAINING_HISTORY",
                feature_schema_version=matrix.feature_schema_version,
                feature_names=matrix.feature_names,
            )

        parameters = self._parameters(request.training_parameters, request.seed)
        feature_names = matrix.feature_names + ("product_level_code", "demand_type_code")
        encoded_rows = self._encoded_rows(matrix)
        split_index = len(encoded_rows) - VALIDATION_ROW_COUNT
        train_x, validation_x = encoded_rows[:split_index], encoded_rows[split_index:]
        train_y, validation_y = matrix.y[:split_index], matrix.y[split_index:]

        model = xgboost.XGBRegressor(**parameters)
        model.fit(train_x, train_y)
        predictions = model.predict(validation_x)
        evidence = tuple(
            ChallengerValidationPrediction(
                target_period=period,
                actual=float(actual),
                predicted=float(predicted),
                error=float(actual) - float(predicted),
                absolute_error=abs(float(actual) - float(predicted)),
                squared_error=(float(actual) - float(predicted)) ** 2,
            )
            for period, actual, predicted in zip(matrix.target_periods[split_index:], validation_y, predictions)
        )
        return XGBoostChallengerTrainingResult(
            status="TRAINED",
            reason_code=None,
            contract_version=CHALLENGER_TRAINING_CONTRACT_VERSION,
            feature_schema_version=matrix.feature_schema_version,
            split_policy_version=TIME_ORDERED_SPLIT_POLICY_VERSION,
            categorical_encoding_version=CATEGORICAL_ENCODING_VERSION,
            xgboost_version=xgboost.__version__,
            seed=request.seed,
            parameters=parameters,
            feature_names=feature_names,
            source_actual_observation_ids=matrix.source_actual_observation_ids,
            source_evidence_signature=self._source_evidence_signature(matrix),
            training_target_periods=matrix.target_periods[:split_index],
            validation_target_periods=matrix.target_periods[split_index:],
            training_count=len(train_y),
            validation_count=len(validation_y),
            validation_predictions=evidence,
            metrics=self._metrics(evidence),
            model=model,
        )

    @staticmethod
    def _source_evidence_signature(matrix) -> str:
        payload = {
            "feature_schema_version": matrix.feature_schema_version,
            "feature_names": matrix.feature_names,
            "X": matrix.X,
            "y": matrix.y,
            "target_periods": matrix.target_periods,
            "source_actual_observation_ids": matrix.source_actual_observation_ids,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def _authorization_tier(evidence: Any | None) -> str | None:
        if evidence is None:
            return None
        return evidence.get("tier") if isinstance(evidence, dict) else getattr(evidence, "tier", None)

    @staticmethod
    def _parameters(overrides: dict[str, Any] | None, seed: int) -> dict[str, Any]:
        parameters = {**_DEFAULT_PARAMETERS, "random_state": seed}
        for name, value in (overrides or {}).items():
            if name not in _DEFAULT_PARAMETERS:
                raise ValueError(f"unsupported challenger training parameter: {name}")
            parameters[name] = value
        return parameters

    @staticmethod
    def _encoded_rows(matrix) -> tuple[tuple[float, ...], ...]:
        try:
            product_code = _PRODUCT_LEVEL_CODES[matrix.product_level]
            demand_code = _DEMAND_TYPE_CODES[matrix.demand_type]
        except KeyError as exc:
            raise ValueError("unsupported deterministic categorical value") from exc
        return tuple(tuple(row) + (product_code, demand_code) for row in matrix.X)

    @staticmethod
    def _metrics(predictions: tuple[ChallengerValidationPrediction, ...]) -> ChallengerMetrics:
        if not predictions:
            return ChallengerMetrics(None, "no_validation_predictions", None, None, None)
        denominator = sum(abs(point.actual) for point in predictions)
        absolute_error = sum(point.absolute_error for point in predictions)
        signed_error = sum(point.error for point in predictions)
        count = len(predictions)
        return ChallengerMetrics(
            wape=None if denominator == 0 else absolute_error / denominator,
            wape_unavailable_reason="zero_actual_denominator" if denominator == 0 else None,
            bias=signed_error / count,
            mae=absolute_error / count,
            rmse=sqrt(sum(point.squared_error for point in predictions) / count),
        )

    @staticmethod
    def _not_trained(
        request: XGBoostChallengerTrainingRequest,
        reason_code: str,
        feature_schema_version: str | None = None,
        feature_names: tuple[str, ...] = (),
    ) -> XGBoostChallengerTrainingResult:
        return XGBoostChallengerTrainingResult(
            status="NOT_ELIGIBLE" if reason_code == "NOT_ELIGIBLE" else "NOT_TRAINABLE",
            reason_code=reason_code,
            contract_version=CHALLENGER_TRAINING_CONTRACT_VERSION,
            feature_schema_version=feature_schema_version,
            split_policy_version=TIME_ORDERED_SPLIT_POLICY_VERSION,
            categorical_encoding_version=CATEGORICAL_ENCODING_VERSION,
            xgboost_version=xgboost.__version__,
            seed=request.seed,
            parameters={},
            feature_names=feature_names,
            source_actual_observation_ids=(),
            source_evidence_signature=None,
            training_target_periods=(),
            validation_target_periods=(),
            training_count=0,
            validation_count=0,
            validation_predictions=(),
            metrics=None,
            model=None,
        )
