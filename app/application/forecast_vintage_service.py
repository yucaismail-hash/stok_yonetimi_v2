"""Projection boundary from durable Forecast result evidence to immutable vintages."""
from datetime import timedelta
from decimal import Decimal
from app.models.dataset import DatasetVersion
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period

class ForecastVintageError(ValueError): pass
_LEVELS={'finished_good','semi_finished_good','raw_material'}

def target_periods(cutoff, horizon):
    parsed=parse_weekly_period(cutoff)
    from datetime import date
    start=date.fromisocalendar(parsed.year, parsed.week, 1)
    return [((start + timedelta(weeks=index)).isocalendar()) for index in range(1,horizon+1)]

def canonical_targets(cutoff, horizon):
    return [f'{item.year:04d}-W{item.week:02d}' for item in target_periods(cutoff,horizon)]

class ForecastVintageService:
    def __init__(self, session): self.session=session
    def project(self, execution, reference, params):
        context=(params or {}).get('forecast_vintage')
        if not isinstance(context,dict): return None
        cutoff=context.get('input_cutoff_period'); demand_type=validate_demand_type(context.get('demand_type'))
        if not cutoff or not demand_type: raise ForecastVintageError('forecast_vintage input_cutoff_period and demand_type are required')
        cutoff=parse_weekly_period(cutoff).period; existing=self.session.query(ForecastVintage).filter_by(runtime_result_reference_id=reference.id).one_or_none()
        if existing: return existing
        self.session.refresh(reference)
        result=reference.inline_result or {}; horizon=result.get('horizon'); items=result.get('items')
        if not isinstance(horizon,int) or horizon<1 or not isinstance(items,list): raise ForecastVintageError('forecast result is not vintage-projectable')
        metadata=context.get('product_metadata') or {}; version=self.session.query(DatasetVersion).filter_by(dataset_id=execution.dataset_id,is_current=True).one_or_none()
        vintage=ForecastVintage(company_id=execution.company_id,execution_id=execution.execution_id,runtime_result_reference_id=reference.id,dataset_id=execution.dataset_id,dataset_version_id=version.id if version else None,forecast_available_at=reference.created_at,forecast_origin_period=cutoff,input_cutoff_period=cutoff,demand_type=demand_type,learning_score_at_run=context.get('learning_score_at_run'),learning_score_version=context.get('learning_score_version'),learning_score_breakdown=context.get('learning_score_breakdown'),learning_score_observed_at=context.get('learning_score_observed_at'),result_version=reference.result_version,contract_version=reference.contract_version)
        self.session.add(vintage); self.session.flush(); targets=canonical_targets(cutoff,horizon)
        for item in items:
            code=item.get('material_code'); values=item.get('forecast'); product=metadata.get(code,{})
            if not isinstance(code,str) or not isinstance(values,list) or len(values)!=horizon or product.get('product_level') not in _LEVELS: raise ForecastVintageError('forecast item metadata is incomplete')
            low=item.get('lower_80') or []; high=item.get('upper_80') or []
            for index,(period,value) in enumerate(zip(targets,values),1):
                self.session.add(ForecastVintagePoint(forecast_vintage_id=vintage.id,material_code=code,target_period=period,forecast_value=Decimal(str(value)),lower_interval=Decimal(str(low[index-1])) if len(low)==horizon else None,upper_interval=Decimal(str(high[index-1])) if len(high)==horizon else None,model_used=item.get('model_used'),selection_metadata=item.get('selection_info'),product_level=product['product_level'],product_group=product.get('product_group'),product_class=product.get('product_class'),horizon_index=index))
        self.session.flush(); return vintage
