"""Adapter from Forecast-ready Dataset input to the existing DemandForecaster."""
from time import perf_counter
from app.analysis.pattern import AdvancedDemandAnalyzer


def forecast_adapter(implementation, prepared_input, request):
    forecaster = implementation(seasonal_periods=52)
    forecaster.set_pattern_analyzer(AdvancedDemandAnalyzer())
    horizon = request.params.get("horizon", 13)
    model_type = request.params.get("model_type", "auto")
    if not isinstance(horizon, int) or horizon <= 0 or not isinstance(model_type, str):
        raise ValueError("invalid forecast parameters")
    started = perf_counter(); items = []
    for item in prepared_input["items"]:
        result = forecaster.forecast(item["demand_history"], horizon=horizon, model_type=model_type)
        items.append({"material_code": item["material_code"], "forecast": result.get("mean", []), "model_used": result.get("model_used"), "selection_info": result.get("selection_info", {}), "lower_80": result.get("lower_80", []), "upper_80": result.get("upper_80", []), "lower_95": result.get("lower_95", []), "upper_95": result.get("upper_95", [])})
    return {"items": items, "horizon": horizon, "warnings": prepared_input.get("warnings", []), "metrics": {"processed_skus": len(items), "adapter_duration_ms": (perf_counter()-started)*1000}}
