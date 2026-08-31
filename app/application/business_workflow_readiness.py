"""Read-only, persisted-evidence eligibility for the integrated Business Workflow."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid_extensions import uuid7

from app.engine.adapters.backtest_adapter import DEFAULT_TEST_WINDOW
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider

_BASE_CAPABILITIES = ("forecast", "safety_stock")


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
    scope_source: str = "LATEST_UPLOAD"
    temporal_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_code": self.material_code,
            "product_name": self.product_name,
            "available_weeks": self.available_weeks,
            "latest_observation_period": self.latest_observation_period,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "scope_source": self.scope_source,
            "temporal_warnings": list(self.temporal_warnings),
        }


@dataclass(frozen=True)
class AnalysisCoverage:
    total_scope_count: int
    fully_analyzed_count: int
    partially_analyzed_count: int
    excluded_count: int
    exclusions: tuple[MaterialCapabilityExclusion, ...]
    scope_mode: str = "LATEST_UPLOAD"
    latest_upload_count: int = 0
    absent_from_latest_upload_count: int = 0
    current_snapshot_warning_count: int = 0
    stale_master_warning_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_scope_count": self.total_scope_count,
            "fully_analyzed_count": self.fully_analyzed_count,
            "partially_analyzed_count": self.partially_analyzed_count,
            "excluded_count": self.excluded_count,
            "exclusions": [item.to_dict() for item in self.exclusions],
            "scope_mode": self.scope_mode,
            "latest_upload_count": self.latest_upload_count,
            "absent_from_latest_upload_count": self.absent_from_latest_upload_count,
            "current_snapshot_warning_count": self.current_snapshot_warning_count,
            "stale_master_warning_count": self.stale_master_warning_count,
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
            snapshot_available = bool(item.get("current_snapshot_available", True))
            rows = []
            for capability in _BASE_CAPABILITIES:
                if available >= base_required:
                    rows.append(CapabilityReadiness(capability, "READY"))
                else:
                    excluded = self._insufficient(capability, code, name, available, base_required, latest)
                    exclusions.append(excluded)
                    rows.append(CapabilityReadiness(capability, "EXCLUDED", excluded.reason_code, excluded.message, base_required, available))
            if available >= backtest_required:
                rows.append(CapabilityReadiness("backtest", "READY"))
            else:
                excluded = self._insufficient("backtest", code, name, available, backtest_required, latest)
                exclusions.append(excluded)
                rows.append(CapabilityReadiness("backtest", "EXCLUDED", excluded.reason_code, excluded.message, backtest_required, available))
            if snapshot_available and available >= base_required:
                rows.append(CapabilityReadiness("simulation", "READY"))
            else:
                reason = "CURRENT_SNAPSHOT_UNAVAILABLE" if not snapshot_available else "INSUFFICIENT_HISTORY"
                message = "Bu ürün son yüklemede bulunmadığı için güncel dönem başı stok bilgisi yok; simülasyon yapılmayacak." if not snapshot_available else f"Bu ürün için simülasyon için en az {base_required} haftalık geçmiş veri gerekir."
                excluded = MaterialCapabilityExclusion(code, name if isinstance(name, str) else None, "simulation", "EXCLUDED", reason, message, available, base_required, latest)
                exclusions.append(excluded)
                rows.append(CapabilityReadiness("simulation", "EXCLUDED", reason, message, base_required, available))
            decision_ready = any(row.capability == "backtest" and row.status == "READY" for row in rows) and any(row.capability == "simulation" and row.status == "READY" for row in rows)
            rows.append(CapabilityReadiness("decision_intelligence", "READY" if decision_ready else "EXCLUDED", None if decision_ready else "DEPENDENCY_NOT_READY", None if decision_ready else "Karar çıktısı için güncel simülasyon ve Geçmiş Performans Testi kanıtı gerekli.", blocked_by=None if decision_ready else "backtest_or_simulation"))
            materials.append(MaterialReadiness(code, name if isinstance(name, str) else None, available, latest, tuple(rows), str(item.get("scope_source") or "LATEST_UPLOAD"), tuple(item.get("temporal_warnings") or ())))

        fully = sum(any(row.capability == "decision_intelligence" and row.status == "READY" for row in material.capabilities) for material in materials)
        partial = sum(any(row.status == "READY" for row in material.capabilities) and not any(row.capability == "decision_intelligence" and row.status == "READY" for row in material.capabilities) for material in materials)
        scope = snapshot.get("scope") if isinstance(snapshot.get("scope"), dict) else {}
        coverage = AnalysisCoverage(len(materials), fully, partial, len(materials) - fully - partial, tuple(exclusions), str(scope.get("scope_mode") or "LATEST_UPLOAD"), int(scope.get("latest_upload_count") or 0), int(scope.get("absent_from_latest_upload_count") or 0), int(scope.get("current_snapshot_warning_count") or 0), int(scope.get("stale_master_warning_count") or 0))
        supplier = snapshot.get("supplier", {})
        supplier_ready = isinstance(supplier, dict) and bool(supplier.get("available"))
        backtest_eligible = sum(any(row.capability == "backtest" and row.status == "READY" for row in material.capabilities) for material in materials)
        backtest_status = "READY" if backtest_eligible == len(materials) and backtest_eligible else "READY_WITH_EXCLUSIONS" if backtest_eligible else "BLOCKED"
        message = None if backtest_status == "READY" else ("Uygun ürünler için Geçmiş Performans Testi yürütülecek; desteklenmeyen ürünler kapsam dışında raporlanacak." if backtest_eligible else "Hiçbir ürün Geçmiş Performans Testi için yeterli geçmiş veriye sahip değil.")
        capabilities = (
            CapabilityReadiness("forecast", "READY" if materials else "BLOCKED", None if materials else "NO_DEMAND_HISTORY", None if materials else "Talep Tahmini için talep geçmişi bulunmuyor."),
            CapabilityReadiness("safety_stock", "READY" if materials else "BLOCKED", None if materials else "NO_DEMAND_HISTORY", None if materials else "Emniyet Stoku için talep geçmişi bulunmuyor."),
            CapabilityReadiness("supplier", "READY" if supplier_ready else "OPTIONAL_UNAVAILABLE", None if supplier_ready else "SUPPLIER_DATA_UNAVAILABLE", None if supplier_ready else "Tedarikçi verisi bulunmadığı için bu adım uygulanmayacak."),
            CapabilityReadiness("simulation", "READY" if fully == len(materials) and fully else "READY_WITH_EXCLUSIONS" if any(any(row.capability == "simulation" and row.status == "READY" for row in material.capabilities) for material in materials) else "BLOCKED", None if any(any(row.capability == "simulation" and row.status == "READY" for row in material.capabilities) for material in materials) else "NO_CURRENT_SNAPSHOT", None if any(any(row.capability == "simulation" and row.status == "READY" for row in material.capabilities) for material in materials) else "Simülasyon için güncel dönem başı stok bilgisi bulunmuyor."),
            CapabilityReadiness("backtest", backtest_status, None if backtest_eligible else "INSUFFICIENT_HISTORY", message, backtest_required, min((material.available_weeks for material in materials), default=0)),
            CapabilityReadiness("decision_intelligence", "READY" if fully else "BLOCKED", None if fully else "DEPENDENCY_NOT_READY", None if fully else "Karar çıktısı için en az bir ürünün zorunlu analiz kanıtı gerekli.", blocked_by=None if fully else "backtest_or_simulation"),
        )
        status = "READY" if fully == len(materials) and fully else "READY_WITH_EXCLUSIONS" if fully else "BLOCKED"
        return BusinessWorkflowReadiness(str(dataset_id), status, capabilities, tuple(materials), coverage)
