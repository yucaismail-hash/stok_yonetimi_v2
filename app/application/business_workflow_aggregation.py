"""Application boundary for durable Business Workflow result aggregation."""
from app.database import SessionLocal
from app.engine.runtime_store import RuntimeStore


class BusinessWorkflowAggregationService:
    def __init__(self, session_factory=SessionLocal):
        self._session_factory=session_factory

    def aggregate(self, company_id, execution_id):
        session=self._session_factory()
        try:
            reference=RuntimeStore(session).aggregate_business_workflow(execution_id,company_id)
            session.commit(); session.refresh(reference)
            return reference.inline_result
        except Exception:
            session.rollback(); raise
        finally:
            session.close()

    def get(self, company_id, execution_id):
        session=self._session_factory()
        try:
            reference=RuntimeStore(session).get_execution_aggregate_result(execution_id,company_id)
            return reference.inline_result if reference else None
        finally:
            session.close()
