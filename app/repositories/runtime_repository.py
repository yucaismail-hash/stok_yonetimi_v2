"""Persistence primitives for canonical runtime tables only."""
from sqlalchemy import and_, update
from app.models.runtime import RuntimeExecution, RuntimeTask, RuntimeTaskAttempt, RuntimeCheckpoint, RuntimeResultReference

class _RuntimeRepository:
    def __init__(self, session, model): self.session, self.model = session, model
    def get(self, identifier, company_id):
        key = self.model.execution_id if self.model is RuntimeExecution else self.model.id
        return self.session.query(self.model).filter(key == identifier, self.model.company_id == company_id).one_or_none()
    def add(self, value): self.session.add(value); self.session.flush(); return value

class RuntimeExecutionRepository(_RuntimeRepository):
    def __init__(self, session): super().__init__(session, RuntimeExecution)
    def conditional_update(self, execution_id, company_id, state, version, values):
        return self.session.execute(update(RuntimeExecution).where(and_(RuntimeExecution.execution_id==execution_id, RuntimeExecution.company_id==company_id, RuntimeExecution.state==state, RuntimeExecution.row_version==version)).values(**values, row_version=RuntimeExecution.row_version + 1)).rowcount

class RuntimeTaskRepository(_RuntimeRepository):
    def __init__(self, session): super().__init__(session, RuntimeTask)
    def by_execution(self, execution_id, company_id): return self.session.query(RuntimeTask).filter_by(execution_id=execution_id, company_id=company_id).order_by(RuntimeTask.task_order).all()

class RuntimeAttemptRepository(_RuntimeRepository):
    def __init__(self, session): super().__init__(session, RuntimeTaskAttempt)
class RuntimeCheckpointRepository(_RuntimeRepository):
    def __init__(self, session): super().__init__(session, RuntimeCheckpoint)
    def latest(self, execution_id, company_id): return self.session.query(RuntimeCheckpoint).filter_by(execution_id=execution_id, company_id=company_id).order_by(RuntimeCheckpoint.checkpoint_version.desc()).first()
class RuntimeResultRepository(_RuntimeRepository):
    def __init__(self, session): super().__init__(session, RuntimeResultReference)
    def by_execution(self, execution_id, company_id): return self.session.query(RuntimeResultReference).filter_by(execution_id=execution_id, company_id=company_id).all()
