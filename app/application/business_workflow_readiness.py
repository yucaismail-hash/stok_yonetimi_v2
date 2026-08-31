"""Read-only, persisted-evidence eligibility for the integrated Business Workflow."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid_extensions import uuid7

from app.engine.adapters.backtest_adapter import DEFAULT_TEST_WINDOW
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider

_BASE_CAPABILITIES = ("forecast", "safety_stock", "simulation")


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
class MaterialCapabilityExclusion:
    material_code: str
    product_name: str | None
    capability: str
    status: str
    reason_code: str
    message: str
    available_weeks: int
    required_weeks: int
    latest_observation_period: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MaterialReadiness:
    material_code: str
    product_name: str | None
    available_weeks: int
    latest_observation_period: str | None
    capabilities: tuple[CapabilityReadiness, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_code": self.material_code,
            "product_name": self.product_name,
            "available_weeks": self.available_weeks,
            "latest_observation_period": self.latest_observation_period,
            "capabilities": [item.to_dict() for item in self.capabilities],
        }


@dataclass(frozen=True)
class AnalysisCoverage:
    total_scope_count: int
    fully_analyzed_count: int
    partially_analyzed_count: int
    excluded_count: int
    exclusions: tuple[MaterialCapabilityExclusion, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_scope_count": self.total_scope_count,
            "fully_analyzed_count": self.fully_analyzed_count,
            "partially_analyzed_count": self.partially_analyzed_count,
            "excluded_count": self.excluded_count,
            "exclusions": [item.to_dict() for item in self.exclusions],
        }


@dataclass(frozen=True)
class BusinessWorkflowReadiness:
    dataset_id: str
    status: str
    capabilities: tuple[CapabilityReadiness, ...]
    materials: tuple[MaterialReadiness, ...] = ()
    coverage: AnalysisCoverage | None = None

    @property
    def is_ready(self) -> bool:
        return self.status in {"READY", "READY_WITH_EXCLUSIONS"}

    def eligible_material_codes(self, capability: str) -> tuple[str, ...]:
        return tuple(
            material.material_code
            for material in self.materials
            if any(item.capability == capability and item.status == "READY" for item in material.capabilities)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "status": self.status,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "materials": [item.to_dict() for item in self.materials],
            "coverage": self.coverage.to_dict() if self.coverage else None,
        }


class BusinessWorkflowReadinessService:
    """Preflight canonical effective history; it never schedules or invokes analytics."""

    def __init__(self, provider_factory=DatasetRuntimeProvider):
        self._provider_factory = provider_factory

    @staticmethod
    def _history(item: dict[str, Any]) -> tuple[int, str | None]:
        history = item.get("demand_history")
        periods = item.get("history_periods")
        latest = periods[-1] if isinstance(periods, list) and periods and isinstance(periods[-1], str) else None
        return (len(history), latest) if isinstance(history, list) else (0, latest)

    @staticmethod
    def _insufficient(capability: str, code: str, name: str | None, available: int, required: int, latest: str | None):
        return MaterialCapabilityExclusion(
            material_code=code, product_name=name, capability=capability, status="EXCLUDED",
            reason_code="INSUFFICIENT_HISTORY",
            message=f"Bu ürün için en az {required} haftalık geçmiş veri gerekir. Mevcut geçmiş: {available} hafta.",
            available_weeks=available, required_weeks=required, latest_observation_period=latest,
        )

    def evaluate(self, session, company_id, user_id, dataset_id, *, params: dict[str, Any] | None = None) -> BusinessWorkflowReadiness:
        configured = dict(params or {})
        test_window = configured.get("test_window", DEFAULT_TEST_WINDOW)
        request = CapabilityExecutionRequest(uuid7(), "business-workflow-readiness", "preflight", Capability.BACKTEST, company_id, user_id, dataset_id, 1, params=configured)
        try:
            snapshot = self._provider_factory(session).preflight(request)
            items = tuple(item for item in snapshot["items"] if isinstance(item, dict) and isinstance(item.get("sku_code"), str))
        except Exception:
            blocked = CapabilityReadiness("forecast", "BLOCKED", "DATASET_INPUT_UNAVAILABLE", "Veri seti işletme analizi için okunamıyor.")
            return BusinessWorkflowReadiness(str(dataset_id), "BLOCKED", (blocked, CapabilityReadiness("decision_intelligence", "BLOCKED", "DEPENDENCY_NOT_READY", "Karar çıktısı gerekli analizler hazır olmadığı için üretilemez.", blocked_by="forecast")))
        if not isinstance(test_window, int) or isinstance(test_window, bool) or test_window < 1:
            blocked = CapabilityReadiness("backtest", "BLOCKED", "INVALID_BACKTEST_WINDOW", "Geçmiş Performans Testi yapılandırması geçerli değil.")
            return BusinessWorkflowReadiness(str(dataset_id), "BLOCKED", (blocked, CapabilityReadiness("decision_intelligence", "BLOCKED", "DEPENDENCY_NOT_READY", "Karar çıktısı gerekli analizler hazır olmadığı için üretilemez.", blocked_by="backtest")))

        base_required, backtest_required = 4, test_window + 4
        materials, exclusions = [], []
        for item in sorted(items, key=lambda value: value["sku_code"]):
            code, name = item["sku_code"], item.get("product_name")
            available, latest = self._history(item)
            rows = []
            for capability in _BASE_CAPABILITIES:
                if available >= base_required:
                    rows.append(CapabilityReadiness(capability, "READY"))
                else:
                    excluded = self._insufficient(capability, code, name, available, base_required, latest)
                    exclusions.append(excluded)
                    rows.append(CapabilityReadiness(capability, "EXCLUDED", excluded.reason_code, excluded.message, base_required, available))
            if available >= backtest_required:
                rows.extend((CapabilityReadiness("backtest", "READY"), CapabilityReadiness("decision_intelligence", "READY")))
            else:
                excluded = self._insufficient("backtest", code, name, available, backtest_required, latest)
                exclusions.append(excluded)
                rows.extend((
                    CapabilityReadiness("backtest", "EXCLUDED", excluded.reason_code, excluded.message, backtest_required, available),
                    CapabilityReadiness("decision_intelligence", "EXCLUDED", "DEPENDENCY_NOT_READY", "Karar çıktısı için Geçmiş Performans Testi kanıtı gerekli.", blocked_by="backtest"),
                ))
            materials.append(MaterialReadiness(code, name if isinstance(name, str) else None, available, latest, tuple(rows)))

        fully = sum(any(row.capability == "backtest" and row.status == "READY" for row in material.capabilities) for material in materials)
        partial = sum(any(row.status == "READY" for row in material.capabilities) and not any(row.capability == "backtest" and row.status == "READY" for row in material.capabilities) for material in materials)
        coverage = AnalysisCoverage(len(materials), fully, partial, len(materials) - fully - partial, tuple(exclusions))
        supplier = snapshot.get("supplier", {})
        supplier_ready = isinstance(supplier, dict) and bool(supplier.get("available"))
        backtest_status = "READY" if fully == len(materials) and fully else "READY_WITH_EXCLUSIONS" if fully else "BLOCKED"
        message = None if backtest_status == "READY" else ("Uygun ürünler için Geçmiş Performans Testi yürütülecek; desteklenmeyen ürünler kapsam dışında raporlanacak." if fully else "Hiçbir ürün Geçmiş Performans Testi için yeterli geçmiş veriye sahip değil.")
        capabilities = (
            CapabilityReadiness("forecast", "READY" if materials else "BLOCKED", None if materials else "NO_DEMAND_HISTORY", None if materials else "Talep Tahmini için talep geçmişi bulunmuyor."),
            CapabilityReadiness("safety_stock", "READY" if materials else "BLOCKED", None if materials else "NO_DEMAND_HISTORY", None if materials else "Emniyet Stoku için talep geçmişi bulunmuyor."),
            CapabilityReadiness("supplier", "READY" if supplier_ready else "OPTIONAL_UNAVAILABLE", None if supplier_ready else "SUPPLIER_DATA_UNAVAILABLE", None if supplier_ready else "Tedarikçi verisi bulunmadığı için bu adım uygulanmayacak."),
            CapabilityReadiness("simulation", "READY" if materials else "BLOCKED", None if materials else "NO_DEMAND_HISTORY", None if materials else "Simülasyon için talep geçmişi bulunmuyor."),
            CapabilityReadiness("backtest", backtest_status, None if fully else "INSUFFICIENT_HISTORY", message, backtest_required, min((material.available_weeks for material in materials), default=0)),
            CapabilityReadiness("decision_intelligence", "READY" if fully else "BLOCKED", None if fully else "DEPENDENCY_NOT_READY", None if fully else "Karar çıktısı için en az bir ürünün zorunlu analiz kanıtı gerekli.", blocked_by=None if fully else "backtest"),
        )
        status = "READY" if fully == len(materials) and fully else "READY_WITH_EXCLUSIONS" if fully else "BLOCKED"
        return BusinessWorkflowReadiness(str(dataset_id), status, capabilities, tuple(materials), coverage)
