"""Acceptance-only durable Business Workflow boundary; it never executes tasks."""
from datetime import datetime, timezone
from dataclasses import dataclass
from uuid import UUID
from uuid_extensions import uuid7
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore
from app.models.runtime import RuntimeExecution
from app.models.dataset import Dataset
from app.services.security import EncryptionService
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider
from app.application.forecast_scope import ForecastScopeService
from app.application.business_workflow_readiness import BusinessWorkflowReadinessService

BUSINESS_WORKFLOW_TYPE='business_workflow'
ACTIVE_BUSINESS_WORKFLOW_STATES=('created','queued','running','waiting','retrying')
TASK_GRAPH=(('forecast','demand_forecast',[]),('safety_stock','safety_stock',['forecast']),('simulation','simulation',['forecast','safety_stock']),('backtest','backtest',['safety_stock']))
SUPPLIER_TASK=('supplier','supplier',['forecast'])

class BusinessWorkflowNotReadyError(ValueError):
 def __init__(self, readiness): self.readiness=readiness; super().__init__('BUSINESS_WORKFLOW_NOT_READY')

@dataclass(frozen=True)
class BusinessWorkflowAcceptanceResult:
 execution_id: UUID
 status: str
 state: str
 progress: float

class BusinessWorkflowAcceptanceService:
 def __init__(self,session_factory=SessionLocal): self._session_factory=session_factory
 def accept(self,company_id:UUID,user_id:UUID,dataset_id:UUID,workflow_version='1.0.0',request_metadata=None,trace_id=None,correlation_id=None):
  """Legacy UUID compatibility facade; use accept_or_resolve for duplicate evidence."""
  return self.accept_or_resolve(company_id,user_id,dataset_id,workflow_version,request_metadata,trace_id,correlation_id).execution_id
 def accept_or_resolve(self,company_id:UUID,user_id:UUID,dataset_id:UUID,workflow_version='1.0.0',request_metadata=None,trace_id=None,correlation_id=None):
  s=self._session_factory()
  try:
   existing=s.query(RuntimeExecution).filter(RuntimeExecution.company_id==company_id,RuntimeExecution.analysis_type==BUSINESS_WORKFLOW_TYPE,RuntimeExecution.state.in_(ACTIVE_BUSINESS_WORKFLOW_STATES)).order_by(RuntimeExecution.created_at.asc()).one_or_none()
   if existing is not None: return BusinessWorkflowAcceptanceResult(existing.execution_id,'ALREADY_RUNNING',existing.state,float(existing.progress))
   supplier=self._supplier_status(s,company_id,user_id,dataset_id)
   graph=(('forecast','demand_forecast',[]),SUPPLIER_TASK,('safety_stock','safety_stock',['forecast','supplier']),('simulation','simulation',['forecast','safety_stock','supplier']),('backtest','backtest',['safety_stock'])) if supplier['available'] else TASK_GRAPH
   metadata=dict(request_metadata or {}); params=dict(metadata.get('params',{})); dataset_config=self._dataset_runtime_config(s,company_id,user_id,dataset_id)
   if dataset_config.get('demand_type') and 'forecast_vintage' not in params:
    params['forecast_vintage']={'demand_type':dataset_config['demand_type']}
   if dataset_config.get('service_level') and 'service_level' not in params: params['service_level']=dataset_config['service_level']
   metadata['params']=ForecastScopeService().enrich(company_id,params)
   readiness=BusinessWorkflowReadinessService().evaluate(s,company_id,user_id,dataset_id,params=metadata['params'])
   if not readiness.is_ready: raise BusinessWorkflowNotReadyError(readiness)
   # The preflight is immutable operational scope for this execution.  Only
   # Backtest and Decision are narrowed here; upstream analytics retain their
   # dataset scope and their partial coverage is reported durably.
   readiness_data=readiness.to_dict()
   metadata['readiness']=readiness_data
   metadata['capability_material_codes']={
    'backtest':list(readiness.eligible_material_codes('backtest')),
    'simulation':list(readiness.eligible_material_codes('simulation')),
    'decision_intelligence':list(readiness.eligible_material_codes('decision_intelligence')),
   }
   metadata['scope_mode']=readiness.coverage.scope_mode if readiness.coverage else 'LATEST_UPLOAD'
   execution=RuntimeExecution(execution_id=uuid7(),company_id=company_id,user_id=user_id,dataset_id=dataset_id,workflow_id='business-'+str(uuid7()),analysis_type=BUSINESS_WORKFLOW_TYPE,state='queued',progress=0,current_stage='planning',accepted_at=datetime.now(timezone.utc),queued_at=datetime.now(timezone.utc),trace_id=trace_id,correlation_id=correlation_id,contract_version='1.0.0',metadata_={'workflow_type':BUSINESS_WORKFLOW_TYPE,'workflow_version':workflow_version,'request_metadata':metadata,'supplier_enrichment':supplier})
   rows=[{'workflow_id':execution.workflow_id,'task_id':tid,'capability':cap,'task_order':i,'required':True,'skippable':False,'dependencies':deps,'state':'pending','max_attempts':3,'timeout_seconds':300} for i,(tid,cap,deps) in enumerate(graph)]
   RuntimeStore(s).create_execution(execution,rows);s.commit();return BusinessWorkflowAcceptanceResult(execution.execution_id,'CREATED',execution.state,float(execution.progress))
  except IntegrityError:
   s.rollback()
   existing=s.query(RuntimeExecution).filter(RuntimeExecution.company_id==company_id,RuntimeExecution.analysis_type==BUSINESS_WORKFLOW_TYPE,RuntimeExecution.state.in_(ACTIVE_BUSINESS_WORKFLOW_STATES)).order_by(RuntimeExecution.created_at.asc()).one_or_none()
   if existing is None: raise
   return BusinessWorkflowAcceptanceResult(existing.execution_id,'ALREADY_RUNNING',existing.state,float(existing.progress))
  except: s.rollback();raise
  finally:s.close()
 def _supplier_status(self,s,company_id,user_id,dataset_id):
  dataset=s.query(Dataset).filter_by(id=dataset_id,company_id=company_id,user_id=user_id,is_active=True).one_or_none()
  if not dataset or not dataset.encrypted_data:return {'available':False,'status':'absent','reason':'authorized supplier dataset is unavailable'}
  try: payload=EncryptionService(s).decrypt_dataset(user_id,dataset.encrypted_data)
  except Exception:return {'available':False,'status':'invalid','reason':'supplier dataset payload cannot be loaded'}
  return DatasetRuntimeProvider.supplier_evidence_status(payload,require_dataset_materials=True)
 def _dataset_runtime_config(self,s,company_id,user_id,dataset_id):
  dataset=s.query(Dataset).filter_by(id=dataset_id,company_id=company_id,user_id=user_id,is_active=True).one_or_none()
  if not dataset or not dataset.encrypted_data:return {}
  try:
   payload=EncryptionService(s).decrypt_dataset(user_id,dataset.encrypted_data)
  except Exception:return {}
  if not isinstance(payload,dict) or payload.get('contract')!='official_v3':return {}
  return {'demand_type':payload.get('demand_type'),'service_level':payload.get('service_level')}
