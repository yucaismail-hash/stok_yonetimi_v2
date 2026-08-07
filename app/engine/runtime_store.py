"""Engine-facing durable runtime facade; not connected to runtime consumers."""
from datetime import datetime, timezone, timedelta
from uuid_extensions import uuid7
from app.engine.enums import ExecutionState
from app.engine.contracts import ExecutionStatusSnapshot
from app.models.runtime import RuntimeExecution, RuntimeTask, RuntimeTaskAttempt, RuntimeCheckpoint, RuntimeResultReference
from app.repositories.runtime_repository import RuntimeExecutionRepository, RuntimeTaskRepository, RuntimeAttemptRepository, RuntimeCheckpointRepository, RuntimeResultRepository

class RuntimeStoreError(RuntimeError): pass
class RuntimeStoreConcurrencyError(RuntimeStoreError): pass
class RuntimeStoreLeaseError(RuntimeStoreError): pass
def _json_safe(value):
    return value is None or isinstance(value,(str,int,float,bool)) or (isinstance(value,list) and all(_json_safe(item) for item in value)) or (isinstance(value,dict) and all(isinstance(key,str) and _json_safe(item) for key,item in value.items()))
_TRANSITIONS={"created":{"queued"},"queued":{"running","cancelled"},"running":{"waiting","retrying","completed","failed","cancelled"},"waiting":{"running","cancelled"},"retrying":{"running","failed","cancelled"}}

class RuntimeStore:
    def __init__(self, session):
        self.session=session; self.executions=RuntimeExecutionRepository(session); self.tasks=RuntimeTaskRepository(session); self.attempts=RuntimeAttemptRepository(session); self.checkpoints=RuntimeCheckpointRepository(session); self.results=RuntimeResultRepository(session)
    def create_execution(self, execution, task_rows):
        existing = None
        if execution.idempotency_key: existing=self.session.query(RuntimeExecution).filter_by(company_id=execution.company_id,idempotency_key=execution.idempotency_key).one_or_none()
        if existing: return existing
        self.executions.add(execution)
        for row in task_rows: self.tasks.add(RuntimeTask(execution_id=execution.execution_id,company_id=execution.company_id,**row))
        return execution
    def get_execution(self, execution_id, company_id): return self.executions.get(execution_id, company_id)
    def get_execution_by_id(self, execution_id): return self.session.query(RuntimeExecution).filter_by(execution_id=execution_id).one_or_none()
    def get_tasks(self, execution_id, company_id): return self.tasks.by_execution(execution_id, company_id)
    def transition_execution(self, execution_id, company_id, expected_state, target_state, expected_row_version, **values):
        if target_state not in _TRANSITIONS.get(expected_state, set()): raise RuntimeStoreError("invalid execution transition")
        if not self.executions.conditional_update(execution_id,company_id,expected_state,expected_row_version,{"state":target_state,**values}): raise RuntimeStoreConcurrencyError("stale execution transition")
        return self.get_execution(execution_id,company_id)
    def request_cancellation(self, execution_id, company_id, expected_row_version):
        execution=self.get_execution(execution_id,company_id)
        if not execution: return None
        return self.transition_execution(execution_id,company_id,execution.state,"cancelled",expected_row_version,cancellation_requested=True,cancelled_at=datetime.now(timezone.utc))
    def get_execution_status(self, execution_id, company_id):
        e=self.get_execution(execution_id,company_id)
        if not e: return None
        retries=sum(t.current_attempt for t in self.get_tasks(execution_id,company_id))
        return ExecutionStatusSnapshot(execution_id=e.execution_id,workflow_id=e.workflow_id,state=ExecutionState(e.state),progress=float(e.progress),updated_at=e.created_at,current_stage=e.current_stage,retry_count=retries,error_summary=str(e.terminal_error) if e.terminal_error else None,trace_id=e.trace_id,correlation_id=e.correlation_id,contract_version=e.contract_version)
    def get_execution_status_by_id(self, execution_id):
        execution = self.get_execution_by_id(execution_id)
        return self.get_execution_status(execution_id, execution.company_id) if execution else None
    def create_checkpoint(self, checkpoint): return self.checkpoints.add(checkpoint)
    def get_latest_checkpoint(self, execution_id, company_id): return self.checkpoints.latest(execution_id,company_id)
    def get_execution_result_references(self, execution_id, company_id): return self.results.by_execution(execution_id,company_id)
    def register_result_reference(self, company_id, execution_id, result_type, result, result_version='1.0.0', contract_version='1.0.0', runtime_task_id=None, runtime_attempt_id=None, validation_status='validated'):
        if not self.get_execution(execution_id, company_id) or not isinstance(result, dict) or not _json_safe(result) or validation_status != 'validated': raise RuntimeStoreError('invalid result reference')
        ref=RuntimeResultReference(company_id=company_id,execution_id=execution_id,runtime_task_id=runtime_task_id,runtime_attempt_id=runtime_attempt_id,result_type=result_type,result_version=result_version,contract_version=contract_version,storage_kind='inline_jsonb',inline_result=result,validation_status=validation_status); self.results.add(ref); self.session.flush(); return ref
    def claim_task(self, execution_id, task_id, company_id, worker_id, lease_seconds, expected_row_version):
        now=datetime.now(timezone.utc); e=self.get_execution(execution_id,company_id)
        task=self.session.query(RuntimeTask).filter_by(execution_id=execution_id,task_id=task_id,company_id=company_id).one_or_none()
        if not e or not task or e.cancellation_requested or e.state in ('completed','failed','cancelled'): raise RuntimeStoreConcurrencyError('task is not claimable')
        claimable = task.state == 'pending' or (task.state == 'running' and task.lease_expires_at and task.lease_expires_at <= now)
        if not claimable or task.row_version != expected_row_version or task.current_attempt >= task.max_attempts: raise RuntimeStoreConcurrencyError('stale task claim')
        token=uuid7(); count=self.session.query(RuntimeTask).filter_by(id=task.id,company_id=company_id,state=task.state,row_version=expected_row_version).update({'state':'running','assigned_worker_id':worker_id,'lease_token':token,'claimed_at':now,'heartbeat_at':now,'lease_expires_at':now+timedelta(seconds=lease_seconds),'current_attempt':task.current_attempt+1,'row_version':task.row_version+1},synchronize_session=False)
        if not count: raise RuntimeStoreConcurrencyError('concurrent task claim')
        if task.state == 'running':
            expired_attempt = self.session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task.id, attempt_number=task.current_attempt, state='running').one_or_none()
            if expired_attempt:
                expired_attempt.state='failed'; expired_attempt.completed_at=now; expired_attempt.duration_ms=(now-expired_attempt.started_at).total_seconds()*1000 if expired_attempt.started_at else None; expired_attempt.retryable=True; expired_attempt.error={'code':'LEASE_EXPIRED'}
        attempt=RuntimeTaskAttempt(company_id=company_id,execution_id=execution_id,runtime_task_id=task.id,attempt_number=task.current_attempt+1,worker_id=worker_id,lease_token=token,state='running',started_at=now); self.attempts.add(attempt); self.session.flush(); self.session.refresh(task); return task,attempt
    def heartbeat_task(self, execution_id, task_id, company_id, lease_token, lease_seconds):
        now=datetime.now(timezone.utc); execution=self.get_execution(execution_id,company_id); task=self.session.query(RuntimeTask).filter_by(execution_id=execution_id,task_id=task_id,company_id=company_id,state='running',lease_token=lease_token).one_or_none()
        if not execution or execution.cancellation_requested or execution.state in ('completed','failed','cancelled') or not task or task.lease_expires_at <= now: raise RuntimeStoreLeaseError('inactive lease')
        task.heartbeat_at=now; task.lease_expires_at=now+timedelta(seconds=lease_seconds); task.row_version+=1; self.session.flush(); return task
    def _progress(self,e):
        tasks=self.get_tasks(e.execution_id,e.company_id); required=[t for t in tasks if t.required]; e.progress=100 if required and all(t.state=='completed' for t in required) else (100*sum(t.state=='completed' for t in required)/len(required) if required else 0)
    def complete_task_attempt(self, execution_id, task_id, company_id, lease_token, result_type, result, result_version='1.0.0', contract_version='1.0.0'):
        execution=self.get_execution(execution_id,company_id)
        if not execution or execution.cancellation_requested or execution.state in ('completed','failed','cancelled'): raise RuntimeStoreLeaseError('execution is not active')
        task=self.session.query(RuntimeTask).filter_by(execution_id=execution_id,task_id=task_id,company_id=company_id,state='running',lease_token=lease_token).one_or_none()
        if not task or task.lease_expires_at <= datetime.now(timezone.utc): raise RuntimeStoreLeaseError('inactive lease')
        attempt=self.session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task.id,attempt_number=task.current_attempt,lease_token=lease_token,state='running').one_or_none()
        if not attempt: raise RuntimeStoreLeaseError('inactive attempt')
        ref=RuntimeResultReference(company_id=company_id,execution_id=execution_id,runtime_task_id=task.id,runtime_attempt_id=attempt.id,result_type=result_type,result_version=result_version,contract_version=contract_version,storage_kind='inline_jsonb',inline_result=result,validation_status='validated'); self.results.add(ref); now=datetime.now(timezone.utc); attempt.state='completed';attempt.completed_at=now;attempt.duration_ms=(now-attempt.started_at).total_seconds()*1000; task.state='completed';task.lease_token=None;task.assigned_worker_id=None;task.lease_expires_at=now;task.completed_at=now;task.row_version+=1; self._progress(self.get_execution(execution_id,company_id)); self.session.flush(); return ref
    def fail_task_attempt(self, execution_id, task_id, company_id, lease_token, error, retryable):
        execution=self.get_execution(execution_id,company_id)
        if not execution or execution.cancellation_requested or execution.state in ('completed','failed','cancelled'): raise RuntimeStoreLeaseError('execution is not active')
        task=self.session.query(RuntimeTask).filter_by(execution_id=execution_id,task_id=task_id,company_id=company_id,state='running',lease_token=lease_token).one_or_none()
        if not task or task.lease_expires_at <= datetime.now(timezone.utc): raise RuntimeStoreLeaseError('inactive lease')
        attempt=self.session.query(RuntimeTaskAttempt).filter_by(runtime_task_id=task.id,attempt_number=task.current_attempt,lease_token=lease_token,state='running').one_or_none(); now=datetime.now(timezone.utc)
        if not attempt: raise RuntimeStoreLeaseError('inactive attempt')
        attempt.state='failed';attempt.completed_at=now;attempt.error=error;attempt.retryable=retryable;task.state='pending' if retryable else 'failed';task.error_summary=error;task.retryable=retryable;task.lease_token=None;task.assigned_worker_id=None;task.lease_expires_at=now;task.row_version+=1;self.session.flush();return task
    def complete_execution(self, execution_id, company_id, expected_row_version):
        return self.transition_execution(execution_id, company_id, 'running', 'completed', expected_row_version, progress=100, current_stage='completed', completed_at=datetime.now(timezone.utc))
    def fail_execution(self, execution_id, company_id, expected_row_version, error):
        return self.transition_execution(execution_id, company_id, 'running', 'failed', expected_row_version, current_stage='forecast', terminal_error=error, completed_at=datetime.now(timezone.utc))
