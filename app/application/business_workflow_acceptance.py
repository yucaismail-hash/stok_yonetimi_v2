"""Acceptance-only durable Business Workflow boundary; it never executes tasks."""
from datetime import datetime, timezone
from uuid import UUID
from uuid_extensions import uuid7
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore
from app.models.runtime import RuntimeExecution
from app.models.dataset import Dataset
from app.services.security import EncryptionService
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider

BUSINESS_WORKFLOW_TYPE='business_workflow'
TASK_GRAPH=(('forecast','demand_forecast',[]),('safety_stock','safety_stock',['forecast']),('simulation','simulation',['forecast','safety_stock']),('backtest','backtest',['safety_stock']))
SUPPLIER_TASK=('supplier','supplier',['forecast'])

class BusinessWorkflowAcceptanceService:
 def __init__(self,session_factory=SessionLocal): self._session_factory=session_factory
 def accept(self,company_id:UUID,user_id:UUID,dataset_id:UUID,workflow_version='1.0.0',request_metadata=None,trace_id=None,correlation_id=None):
  s=self._session_factory()
  try:
   supplier=self._supplier_status(s,company_id,user_id,dataset_id)
   graph=(('forecast','demand_forecast',[]),SUPPLIER_TASK,('safety_stock','safety_stock',['forecast','supplier']),('simulation','simulation',['forecast','safety_stock','supplier']),('backtest','backtest',['safety_stock'])) if supplier['available'] else TASK_GRAPH
   execution=RuntimeExecution(execution_id=uuid7(),company_id=company_id,user_id=user_id,dataset_id=dataset_id,workflow_id='business-'+str(uuid7()),analysis_type=BUSINESS_WORKFLOW_TYPE,state='queued',progress=0,current_stage='planning',accepted_at=datetime.now(timezone.utc),queued_at=datetime.now(timezone.utc),trace_id=trace_id,correlation_id=correlation_id,contract_version='1.0.0',metadata_={'workflow_type':BUSINESS_WORKFLOW_TYPE,'workflow_version':workflow_version,'request_metadata':request_metadata or {},'supplier_enrichment':supplier})
   rows=[{'workflow_id':execution.workflow_id,'task_id':tid,'capability':cap,'task_order':i,'required':True,'skippable':False,'dependencies':deps,'state':'pending','max_attempts':1,'timeout_seconds':300} for i,(tid,cap,deps) in enumerate(graph)]
   RuntimeStore(s).create_execution(execution,rows);s.commit();return execution.execution_id
  except: s.rollback();raise
  finally:s.close()
 def _supplier_status(self,s,company_id,user_id,dataset_id):
  dataset=s.query(Dataset).filter_by(id=dataset_id,company_id=company_id,user_id=user_id,is_active=True).one_or_none()
  if not dataset or not dataset.encrypted_data:return {'available':False,'status':'absent','reason':'authorized supplier dataset is unavailable'}
  try: payload=EncryptionService(s).decrypt_dataset(user_id,dataset.encrypted_data)
  except Exception:return {'available':False,'status':'invalid','reason':'supplier dataset payload cannot be loaded'}
  return DatasetRuntimeProvider.supplier_evidence_status(payload,require_dataset_materials=True)
