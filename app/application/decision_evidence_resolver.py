"""Canonical, read-only decision evidence normalization."""
from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from app.database import SessionLocal
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.models.runtime import RuntimeExecution, RuntimeResultReference
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.event_intelligence_memory import EventIntelligenceMemory
from app.models.supplier_learning_memory import SupplierLearningMemory
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry
from app.models.retraining_job import RetrainingJob
from app.models.model_artifact import ModelArtifact
from datetime import date
from app.services.dataset.weekly_normalization import parse_weekly_period
from app.services.dataset.ingestion_policy import validate_demand_type

@dataclass(frozen=True)
class DecisionEvidenceEnvelope:
 company_id: object; material_code: str; demand_type: str; decision_cutoff_period: str; decision_context: str
 status: str; required: tuple; optional: tuple; hints: tuple; fingerprint: str

class DecisionEvidenceResolver:
 """Uses only durable compact projections and runtime references; never writes."""
 _REQUIRED={'FORECAST_REVIEW':('forecast',),'REPLENISHMENT':('forecast','safety_stock'),'SAFETY_STOCK':('forecast','safety_stock'),'SUPPLIER_REVIEW':()}
 def __init__(self,session_factory=SessionLocal): self._sf=session_factory
 def resolve(self,company_id,material_code,demand_type,decision_cutoff_period,decision_context):
  demand=validate_demand_type(demand_type); cutoff=parse_weekly_period(decision_cutoff_period).period; context=str(decision_context).upper(); s=self._sf()
  try:
   required=[]; optional=[]
   forecast=self._forecast(s,company_id,material_code,demand,cutoff); safety=self._runtime(s,company_id,'safety_stock',material_code,cutoff,demand); supplier=self._runtime(s,company_id,'supplier',material_code,cutoff,demand); simulation=self._runtime(s,company_id,'simulation',material_code,cutoff,demand); backtest=self._runtime(s,company_id,'backtest',material_code,cutoff,demand)
   rows={'forecast':forecast,'safety_stock':safety,'supplier_operational':supplier,'simulation':simulation,'backtest':backtest,'pattern':self._pattern(s,company_id,material_code,demand,cutoff),'company_learning':self._company(s,company_id),'event':self._events(s,company_id,material_code,demand,cutoff),'supplier_learning':self._supplier_learning(s,company_id,material_code,cutoff),'champion':self._champion(s,company_id,material_code,demand),'retraining':self._retraining(s,company_id,material_code,demand)}
   required_names=self._REQUIRED.get(context,('forecast',))
   for name in required_names: required.append((name,rows[name]))
   for name,value in rows.items():
    if name not in required_names: optional.append((name,value))
   status='READY' if all(value['status']=='AVAILABLE' for _,value in required) else 'INSUFFICIENT_REQUIRED_EVIDENCE'
   hints=tuple(sorted((name,self._hint(value)) for name,value in rows.items() if value['status']=='AVAILABLE'))
   semantic={'company_id':str(company_id),'material_code':material_code,'demand_type':demand,'cutoff':cutoff,'context':context,'required':required,'optional':optional}
   fp=sha256(dumps(semantic,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
   return DecisionEvidenceEnvelope(company_id,material_code,demand,cutoff,context,status,tuple(required),tuple(optional),hints,fp)
  finally:s.close()
 @staticmethod
 def _compatible(value,cutoff):
  a,b=parse_weekly_period(value),parse_weekly_period(cutoff);return(a.year,a.week)<=(b.year,b.week)
 @staticmethod
 def _status(row,cutoff=None,cutoff_attr='cutoff_period'):
  if row is None:return {'status':'ABSENT'}
  if cutoff is not None and not DecisionEvidenceResolver._compatible(getattr(row,cutoff_attr),cutoff):return {'status':'INCOMPATIBLE','reason':'FUTURE_EVIDENCE'}
  return {'status':'AVAILABLE','source_id':str(row.id)}
 def _forecast(self,s,c,m,d,cutoff):
  rows=s.query(ForecastVintage).join(ForecastVintagePoint).filter(ForecastVintage.company_id==c,ForecastVintage.demand_type==d,ForecastVintagePoint.material_code==m).order_by(ForecastVintage.forecast_available_at.desc()).all()
  row=next((x for x in rows if self._compatible(x.input_cutoff_period,cutoff)),None)
  out=self._status(row,cutoff,'input_cutoff_period');
  if row:out.update({'runtime_result_reference_id':str(row.runtime_result_reference_id),'cutoff_period':row.input_cutoff_period,'versions':(row.result_version,row.contract_version)})
  return out
 def _runtime(self,s,c,kind,m,cutoff,demand_type=None):
  pairs=s.query(RuntimeResultReference,RuntimeExecution).join(RuntimeExecution,RuntimeResultReference.execution_id==RuntimeExecution.execution_id).filter(RuntimeResultReference.company_id==c,RuntimeResultReference.result_type==kind,RuntimeResultReference.validation_status=='validated',RuntimeExecution.state=='completed').order_by(RuntimeResultReference.created_at.desc()).all()
  scoped=[pair for pair in pairs if self._result_has_material(pair[0].inline_result,m) and self._runtime_demand_matches(pair[1],demand_type)]
  compatible=[]; known_future=False
  for ref,execution in scoped:
   source_cutoff=self._runtime_cutoff(execution)
   if source_cutoff is None: continue
   if self._compatible(source_cutoff,cutoff): compatible.append((ref,source_cutoff))
   else: known_future=True
  if not compatible:
   if not scoped:return {'status':'ABSENT'}
   return {'status':'INCOMPATIBLE','reason':'FUTURE_EVIDENCE' if known_future else 'CUTOFF_UNKNOWN'}
  row,source_cutoff=compatible[0]
  return {'status':'AVAILABLE','source_id':str(row.id),'runtime_result_reference_id':str(row.id),'result_version':row.result_version,'contract_version':row.contract_version,'cutoff_period':source_cutoff}
 def _pattern(self,s,c,m,d,cutoff):
  row=s.query(PatternLearningMemory).filter_by(company_id=c,material_code=m,demand_type=d).one_or_none();out=self._status(row,cutoff)
  if row:out.update({'classification':row.pattern_classification,'confidence':str(row.confidence),'cutoff_period':row.cutoff_period,'fingerprint':row.source_pattern_fingerprint})
  return out
 def _company(self,s,c):
  row=s.query(CompanyLearningMemoryV2).filter_by(company_id=c).one_or_none();out=self._status(row)
  if row:out.update({'maturity_score':str(row.evidence_maturity_score),'maturity_level':row.evidence_maturity_level,'fingerprint':row.source_summary_fingerprint})
  return out
 def _events(self,s,c,m,d,cutoff):
  rows=s.query(EventIntelligenceMemory).filter_by(company_id=c,material_code=m,demand_type=d).order_by(EventIntelligenceMemory.event_identity).all();ok=[r for r in rows if self._compatible(r.cutoff_period,cutoff)]
  if not ok:return {'status':'INCOMPATIBLE' if rows else 'ABSENT','reason':'FUTURE_EVIDENCE' if rows else None,'entries':[]}
  return {'status':'AVAILABLE','entries':tuple({'source_id':str(r.id),'event_identity':r.event_identity,'classification':r.classification,'cutoff_period':r.cutoff_period,'fingerprint':r.source_fingerprint,'confounded':bool(r.overlap_confounded)} for r in ok)}
 def _supplier_learning(self,s,c,m,cutoff):
  rows=s.query(SupplierLearningMemory).filter_by(company_id=c,material_code=m).order_by(SupplierLearningMemory.supplier_id).all()
  parsed=parse_weekly_period(cutoff); cutoff_date=date.fromisocalendar(parsed.year,parsed.week,7)
  compatible=[r for r in rows if r.cutoff_date<=cutoff_date]
  if not compatible:return {'status':'INCOMPATIBLE' if rows else 'ABSENT','reason':'FUTURE_EVIDENCE' if rows else None,'entries':()}
  return {'status':'AVAILABLE','entries':tuple({'source_id':str(r.id),'classification':r.classification,'fingerprint':r.source_fingerprint,'cutoff_date':str(r.cutoff_date)} for r in compatible)}
 def _champion(self,s,c,m,d):
  cur=s.query(ChampionRegistryCurrent).filter_by(company_id=c,material_code=m,demand_type=d).one_or_none()
  if not cur:return {'status':'ABSENT'}
  row=s.query(ChampionRegistryEntry).filter_by(id=cur.active_entry_id,company_id=c).one_or_none()
  if row is None:return {'status':'INCOMPATIBLE','reason':'POINTER_INVALID'}
  artifact=s.query(ModelArtifact).filter_by(id=row.model_artifact_id,company_id=c).one_or_none() if row.model_artifact_id else None
  return {'status':'AVAILABLE','source_id':str(row.id),'entry_type':row.entry_type,'classical_strategy':row.classical_strategy,'model_artifact_id':str(row.model_artifact_id) if row.model_artifact_id else None,'artifact_checksum':artifact.artifact_checksum if artifact else None}
 def _retraining(self,s,c,m,d):
  row=s.query(RetrainingJob).filter_by(company_id=c,material_code=m,demand_type=d).order_by(RetrainingJob.created_at.desc()).first();return {'status':'ABSENT'} if row is None else {'status':'AVAILABLE','source_id':str(row.id),'state':row.state,'training_cutoff_period':row.training_cutoff_period,'fingerprint':row.candidate_fingerprint}
 @staticmethod
 def _hint(value):return value.get('classification') or value.get('entry_type') or value.get('status')
 @staticmethod
 def _result_has_material(result,material_code):
  if not isinstance(result,dict): return False
  items=result.get('items')
  if not isinstance(items,list): return False
  return any(isinstance(item,dict) and item.get('material_code')==material_code for item in items)
 @staticmethod
 def _runtime_cutoff(execution):
  metadata=execution.metadata_ or {}; request_metadata=metadata.get('request_metadata') or {}
  params=metadata.get('params') or request_metadata.get('params') or request_metadata or {}
  context=params.get('forecast_vintage') if isinstance(params.get('forecast_vintage'),dict) else {}
  value=params.get('analysis_cutoff_period') or params.get('forecast_cutoff_period') or context.get('input_cutoff_period')
  try:return parse_weekly_period(value).period if value else None
  except (TypeError,ValueError):return None
 @staticmethod
 def _runtime_demand_matches(execution,demand_type):
  """Keep runtime evidence inside its persisted request scope when present.

  Legacy standalone references may predate explicit demand metadata; those
  retain their material-only compatibility behavior.  Once a request records
  a demand type, a resolver for another demand series must not consume it.
  """
  if demand_type is None:return True
  metadata=execution.metadata_ or {}; request_metadata=metadata.get('request_metadata') or {}
  params=metadata.get('params') or request_metadata.get('params') or request_metadata or {}
  context=params.get('forecast_vintage') if isinstance(params.get('forecast_vintage'),dict) else {}
  persisted=params.get('demand_type') or context.get('demand_type')
  return persisted is None or persisted==demand_type
