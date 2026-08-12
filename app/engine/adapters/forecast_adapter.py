"""Adapter from Forecast-ready Dataset input to the Champion-resolved Forecast path."""
from time import perf_counter
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.application.champion_resolver import ChampionResolver
from app.application.xgboost_champion_inference import XGBoostChampionInferenceService


def forecast_adapter(implementation, prepared_input, request, resolver_factory=ChampionResolver, inference_factory=XGBoostChampionInferenceService):
    forecaster = implementation(seasonal_periods=52)
    forecaster.set_pattern_analyzer(AdvancedDemandAnalyzer())
    horizon = request.params.get("horizon", 13)
    model_type = request.params.get("model_type", "auto")
    if not isinstance(horizon, int) or horizon <= 0 or not isinstance(model_type, str):
        raise ValueError("invalid forecast parameters")
    context=request.params.get('forecast_vintage') if isinstance(request.params.get('forecast_vintage'),dict) else {}
    cutoff=request.params.get('forecast_cutoff_period',context.get('input_cutoff_period'))
    demand_type=request.params.get('demand_type',context.get('demand_type'))
    resolver=resolver_factory() if isinstance(cutoff,str) and isinstance(demand_type,str) else None
    started = perf_counter(); items = []
    for item in prepared_input["items"]:
        code=item["material_code"]; resolution=None
        if resolver is not None:
            try: resolution=resolver.resolve(request.company_id,code,demand_type,cutoff)
            except LookupError: resolution=None
        if resolution is not None and resolution.kind=='XGBOOST_ARTIFACT':
            prediction=inference_factory().predict(request.company_id,code,demand_type,cutoff,horizon)
            info={'champion_resolution':'xgboost_artifact','champion_registry_entry_id':str(prediction.champion_registry_entry_id),'model_artifact_id':str(prediction.model_artifact_id),'artifact_checksum':prediction.artifact_checksum,'feature_schema_version':prediction.feature_schema_version,'inference_strategy_version':prediction.inference_strategy_version,'training_cutoff_period':prediction.training_cutoff_period,'forecast_cutoff_period':cutoff,'demand_type':demand_type}
            items.append({'material_code':code,'forecast':list(prediction.forecast_values),'model_used':'xgboost_champion','selection_info':info,'lower_80':[],'upper_80':[],'lower_95':[],'upper_95':[]})
            continue
        result=forecaster.forecast(item['demand_history'],horizon=horizon,model_type=model_type)
        info=dict(result.get('selection_info',{}))
        if resolution is not None:
            info.update({'champion_resolution':'fallback_classical' if resolution.fallback else 'classical_existing','champion_registry_entry_id':str(resolution.registry_entry_id),'classical_strategy':'demand_forecaster_auto_v1'})
            if resolution.fallback: info['fallback_reason']=resolution.reason_code
        items.append({'material_code':code,'forecast':result.get('mean',[]),'model_used':result.get('model_used'),'selection_info':info,'lower_80':result.get('lower_80',[]),'upper_80':result.get('upper_80',[]),'lower_95':result.get('lower_95',[]),'upper_95':result.get('upper_95',[])})
    return {"items": items, "horizon": horizon, "warnings": prepared_input.get("warnings", []), "metrics": {"processed_skus": len(items), "adapter_duration_ms": (perf_counter()-started)*1000}}
