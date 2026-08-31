"""Read-only, backend-authoritative eligibility for the integrated Business Workflow."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid_extensions import uuid7

from app.engine.adapters.backtest_adapter import DEFAULT_TEST_WINDOW
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider


@dataclass(frozen=True)
class CapabilityReadiness:
    capability: str
    status: str
    reason_code: str | None = None
    message: str | None = None
    required_weeks: int | None = None
    available_weeks: int | None = None
    blocked_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BusinessWorkflowReadiness:
    dataset_id: str
    status: str
    capabilities: tuple[CapabilityReadiness, ...]

    @property
    def is_ready(self) -> bool:
        return self.status == "READY"

    def to_dict(self) -> dict[str, Any]:
        return {"dataset_id": self.dataset_id, "status": self.status, "capabilities": [item.to_dict() for item in self.capabilities]}


class BusinessWorkflowReadinessService:
    """Preflights mandatory input contracts without scheduling or invoking analytics."""

    def __init__(self, provider_factory=DatasetRuntimeProvider):
        self._provider_factory = provider_factory

    def evaluate(self, session, company_id, user_id, dataset_id, *, params: dict[str, Any] | None = None) -> BusinessWorkflowReadiness:
        configured = dict(params or {})
        test_window = configured.get("test_window", DEFAULT_TEST_WINDOW)
        request = CapabilityExecutionRequest(uuid7(), "business-workflow-readiness", "preflight", Capability.BACKTEST, company_id, user_id, dataset_id, 1, params=configured)
        try:
            snapshot = self._provider_factory(session).preflight(request)
            items = snapshot["items"]
        except Exception:
            blocked = CapabilityReadiness("forecast", "BLOCKED", "DATASET_INPUT_UNAVAILABLE", "Veri seti işletme analizi için okunamıyor.")
            return BusinessWorkflowReadiness(str(dataset_id), "BLOCKED", (blocked, CapabilityReadiness("decision_intelligence", "BLOCKED", "DEPENDENCY_NOT_READY", "Karar çıktısı gerekli analizler hazır olmadığı için üretilemez.", blocked_by="forecast")))

        histories = [item.get("demand_history", []) for item in items if isinstance(item, dict)]
        if not isinstance(test_window, int) or isinstance(test_window, bool) or test_window < 1:
            backtest = CapabilityReadiness("backtest", "BLOCKED", "INVALID_BACKTEST_WINDOW", "Geçmiş Performans Testi yapılandırması geçerli değil.")
        else:
            required = test_window + 4
            available = min((len(history) for history in histories if isinstance(history, list)), default=0)
            if not histories:
                backtest = CapabilityReadiness("backtest", "BLOCKED", "NO_DEMAND_HISTORY", "Geçmiş Performans Testi için talep geçmişi bulunmuyor.", required_weeks=required, available_weeks=0)
            elif available < required:
                backtest = CapabilityReadiness("backtest", "BLOCKED", "INSUFFICIENT_HISTORY", f"Geçmiş Performans Testi için en az {required} haftalık geçmiş veri gerekir. Mevcut veri setinizde {available} hafta bulunuyor.", required_weeks=required, available_weeks=available)
            else:
                backtest = CapabilityReadiness("backtest", "READY")

        supplier = snapshot.get("supplier", {})
        supplier_ready = isinstance(supplier, dict) and bool(supplier.get("available"))
        capabilities = [
            CapabilityReadiness("forecast", "READY" if histories else "BLOCKED", None if histories else "NO_DEMAND_HISTORY", None if histories else "Talep Tahmini için talep geçmişi bulunmuyor."),
            CapabilityReadiness("safety_stock", "READY" if histories else "BLOCKED", None if histories else "NO_DEMAND_HISTORY", None if histories else "Emniyet Stoku için talep geçmişi bulunmuyor."),
            CapabilityReadiness("supplier", "READY" if supplier_ready else "OPTIONAL_UNAVAILABLE", None if supplier_ready else "SUPPLIER_DATA_UNAVAILABLE", None if supplier_ready else "Tedarikçi verisi bulunmadığı için bu adım uygulanmayacak."),
            CapabilityReadiness("simulation", "READY" if histories else "BLOCKED", None if histories else "NO_DEMAND_HISTORY", None if histories else "Simülasyon için talep geçmişi bulunmuyor."),
            backtest,
        ]
        blockers = [item.capability for item in capabilities if item.status == "BLOCKED"]
        capabilities.append(CapabilityReadiness("decision_intelligence", "READY" if not blockers else "BLOCKED", None if not blockers else "DEPENDENCY_NOT_READY", None if not blockers else "Karar çıktısı gerekli analizler hazır olmadığı için üretilemez.", blocked_by=blockers[0] if blockers else None))
        return BusinessWorkflowReadiness(str(dataset_id), "READY" if not blockers else "BLOCKED", tuple(capabilities))
