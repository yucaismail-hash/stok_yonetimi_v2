"""Forecast-only persisted Dataset provider for capability execution."""
from app.engine.capability_registry import Capability
from app.engine.capability_executor import CapabilityInputValidationError, DatasetInputUnavailableError
from app.models.dataset import Dataset
from app.services.security import EncryptionService


class DatasetRuntimeProvider:
    def __init__(self, session, encryption_service_factory=EncryptionService):
        self._session = session
        self._encryption_service_factory = encryption_service_factory

    def __call__(self, request):
        if request.capability is not Capability.DEMAND_FORECAST:
            raise DatasetInputUnavailableError("capability dataset input is unavailable")
        dataset = self._session.query(Dataset).filter_by(id=request.dataset_id, company_id=request.company_id, user_id=request.user_id, is_active=True).one_or_none()
        if not dataset:
            raise DatasetInputUnavailableError("authorized dataset is unavailable")
        if not dataset.encrypted_data:
            raise CapabilityInputValidationError("dataset payload is unavailable")
        try:
            payload = self._encryption_service_factory(self._session).decrypt_dataset(request.user_id, dataset.encrypted_data)
        except Exception as exc:
            raise DatasetInputUnavailableError("dataset payload cannot be loaded") from exc
        items = payload.get("items", []) if isinstance(payload, dict) else []
        requested = set(request.material_codes or [])
        selected = []
        found = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            code = item.get("sku_code")
            if not isinstance(code, str) or (requested and code not in requested):
                continue
            history = item.get("demand_history", [])
            if not isinstance(history, list) or len(history) < 4 or not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in history):
                continue
            selected.append({"material_code": code, "demand_history": list(history)})
            found.add(code)
        missing = sorted(requested - found)
        if missing:
            raise CapabilityInputValidationError("requested material codes are unavailable")
        if not selected:
            raise CapabilityInputValidationError("no forecast-ready demand history is available")
        return {"items": selected, "warnings": [], "dataset_id": str(dataset.id)}
