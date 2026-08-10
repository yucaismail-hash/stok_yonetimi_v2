"""Adapter from DatasetRuntimeProvider inputs to the real Safety Stock optimizer."""
from time import perf_counter

from app.engine.capability_executor import CapabilityInputValidationError


SYSTEM_DEFAULT_SERVICE_LEVEL = 0.95


def _service_level(params):
    value = params.get("service_level", {"mode": "automatic"})
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = {"mode": "manual", "value": value}
    if not isinstance(value, dict):
        raise CapabilityInputValidationError("service_level must be automatic or manual(value)")
    mode = value.get("mode", "automatic")
    if mode == "automatic":
        return SYSTEM_DEFAULT_SERVICE_LEVEL, {"mode": "automatic", "source": "system_default"}
    manual = value.get("value")
    if mode != "manual" or isinstance(manual, bool) or not isinstance(manual, (int, float)) or not 0 < manual < 1:
        raise CapabilityInputValidationError("manual service_level must be a number strictly between 0 and 1")
    return float(manual), {"mode": "manual", "source": "request"}


def safety_stock_adapter(implementation, prepared_input, request):
    service_level, service_level_metadata = _service_level(request.params)
    optimizer = implementation()
    started = perf_counter(); items = []
    for item in prepared_input["items"]:
        source_lead_time_days = item["lead_time_days"]
        if not float(source_lead_time_days).is_integer():
            raise CapabilityInputValidationError("lead_time_days must be whole days for the Safety Stock optimizer")
        effective_lead_time_days = int(source_lead_time_days)
        candidates = optimizer.calculate_all_methods(item["demand_history"], effective_lead_time_days, service_level)
        # Optimizer returns numpy scalar values; normalize only the boundary representation.
        candidates = {name: float(value) for name, value in candidates.items()}
        items.append({
            "material_code": item["material_code"], "safety_stock": candidates["hybrid_ss"],
            "selected_method": "hybrid_ss", "candidate_methods": candidates,
            "service_level": service_level, "service_level_metadata": service_level_metadata,
            "demand_observations": len(item["demand_history"]),
            "zero_ratio": float(sum(value == 0 for value in item["demand_history"]) / len(item["demand_history"])),
            "source_lead_time_days": source_lead_time_days, "effective_lead_time_used": effective_lead_time_days,
            "effective_unit": "days", "supplier_enrichment": item["supplier_enrichment"], "lead_time_source": item["supplier_enrichment"].get("lead_time_source", "dataset_manual"),
        })
    return {"items": items, "service_level": service_level, "service_level_metadata": service_level_metadata,
            "warnings": [], "metrics": {"processed_skus": len(items), "candidate_method_count": 6,
            "adapter_duration_ms": (perf_counter() - started) * 1000}}
