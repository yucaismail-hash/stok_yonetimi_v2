"""Durable, canonical Forecast scope preparation at dispatch time."""
from copy import deepcopy
from uuid import UUID
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation
from app.models.runtime import RuntimeExecution
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period

class ForecastScopeError(ValueError): pass

class ForecastScopeService:
 def __init__(self,session_factory=SessionLocal):self._session_factory=session_factory
 def enrich(self,company_id,params,material_codes=None):
  values=deepcopy(params or {});context=values.get('forecast_vintage')
  if context is None:return values
  if not isinstance(context,dict):raise ForecastScopeError('forecast_vintage must be an object')
  mode=values.get('scope_mode',context.get('scope_mode','current_canonical'))
  if mode=='replay_snapshot':return self._replay(company_id,values,context,material_codes)
  if mode!='current_canonical':raise ForecastScopeError('unsupported forecast scope_mode')
  demand=validate_demand_type(context.get('demand_type',values.get('demand_type')))
  if demand is None:raise ForecastScopeError('authoritative forecast demand_type is required')
  s=self._session_factory()
  try:
   query=s.query(ActualWeeklyObservation.period).filter_by(company_id=company_id,demand_type=demand)
   if material_codes:query=query.filter(ActualWeeklyObservation.material_code.in_(material_codes))
   periods=[parse_weekly_period(row[0]).period for row in query.all()]
   if not periods:raise ForecastScopeError('canonical accepted Actual history is required for forecast scope')
   cutoff=max(periods,key=lambda value:(parse_weekly_period(value).year,parse_weekly_period(value).week))
  finally:s.close()
  declared=context.get('input_cutoff_period',values.get('forecast_cutoff_period'))
  if declared is not None and parse_weekly_period(declared).period!=cutoff:raise ForecastScopeError('declared forecast cutoff disagrees with canonical Actual history')
  context={**context,'demand_type':demand,'input_cutoff_period':cutoff,'scope_mode':'current_canonical'};values.update({'scope_mode':'current_canonical','demand_type':demand,'forecast_cutoff_period':cutoff,'forecast_vintage':context});return values
 def _replay(self,company_id,values,context,material_codes):
  source=values.get('source_execution_id',context.get('source_execution_id'))
  try:source_id=UUID(str(source))
  except (TypeError,ValueError) as exc:raise ForecastScopeError('trusted replay source_execution_id is required') from exc
  s=self._session_factory()
  try:
   execution=s.query(RuntimeExecution).filter_by(execution_id=source_id,company_id=company_id).one_or_none()
   if execution is None:raise ForecastScopeError('trusted replay source execution is unavailable')
   metadata=execution.metadata_ or {};source_params=metadata.get('params') or (metadata.get('request_metadata') or {}).get('params') or {};source_context=source_params.get('forecast_vintage') or {}
   demand=source_params.get('demand_type',source_context.get('demand_type'));cutoff=source_params.get('forecast_cutoff_period',source_context.get('input_cutoff_period'))
   if validate_demand_type(demand) is None or not cutoff:raise ForecastScopeError('source execution has no authoritative forecast scope')
   requested=context.get('demand_type',values.get('demand_type'));declared=context.get('input_cutoff_period',values.get('forecast_cutoff_period'))
   if requested is not None and requested!=demand:raise ForecastScopeError('replay demand_type conflicts with source execution')
   if declared is not None and parse_weekly_period(declared).period!=parse_weekly_period(cutoff).period:raise ForecastScopeError('replay cutoff conflicts with source execution')
   source_materials=metadata.get('material_codes');
   if material_codes and source_materials and set(material_codes)!=set(source_materials):raise ForecastScopeError('replay material scope conflicts with source execution')
  finally:s.close()
  replay_context={**context,'demand_type':demand,'input_cutoff_period':cutoff,'scope_mode':'replay_snapshot','source_execution_id':str(source_id)}
  values.update({'scope_mode':'replay_snapshot','source_execution_id':str(source_id),'source_forecast_cutoff_period':cutoff,'demand_type':demand,'forecast_cutoff_period':cutoff,'forecast_vintage':replay_context});return values
