"""Incremental, scope-based refresh façade for Pattern Learning Memory."""
from dataclasses import dataclass
from time import perf_counter

from app.application.pattern_learning_materialization import PatternLearningMaterializationService
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period

@dataclass(frozen=True)
class PatternRefreshResult:
 company_id:object;material_code:str;demand_type:str;requested_cutoff_period:str;status:str
 memory_id:object|None;previous_fingerprint:str|None;source_fingerprint:str|None;previous_row_version:int|None;row_version:int|None;duration_ms:float;failure_code:str|None=None

class PatternLearningRefreshService:
 """Refreshes exactly one supplied dirty scope; it never discovers/scans scopes."""
 def __init__(self,materialization_service=None,*,before_materialize=None,after_materialize=None):
  self._materializer=materialization_service or PatternLearningMaterializationService()
  self._before=before_materialize;self._after=after_materialize
 def refresh(self,company_id,material_code,demand_type,cutoff_period):
  started=perf_counter();demand=validate_demand_type(demand_type);cutoff=parse_weekly_period(cutoff_period).period
  previous=self._materializer.get_current(company_id,material_code,demand)
  if self._before:self._before(company_id,material_code,demand,cutoff)
  result=self._materializer.materialize(company_id,material_code,demand,cutoff)
  response=PatternRefreshResult(company_id,material_code,demand,cutoff,result.status,result.memory_id,previous.source_pattern_fingerprint if previous else None,result.source_pattern_fingerprint,previous.row_version if previous else None,result.row_version,(perf_counter()-started)*1000)
  if self._after:self._after(response)
  return response
 def refresh_batch(self,requests):
  """Caller-selected bounded scopes only; no global discovery or rescan."""
  return tuple(self.refresh(**request) for request in requests)
