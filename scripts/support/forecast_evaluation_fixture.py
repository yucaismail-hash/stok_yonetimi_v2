"""Shared primitive-ID fixture contract for persisted forecast evaluation probes.

Production services remain authoritative; this module is intentionally test-only.
"""
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class ForecastEvaluationFixtureIds:
    company_id: UUID
    user_id: UUID
    dataset_id: UUID
    execution_id: UUID
    evaluation_id: UUID
    material_code: str
    demand_type: str

def cleanup_fixture(session, ids, models):
    """Delete only exact fixture identities, ordered by their persisted dependencies.

    `models` is supplied by the caller to keep this support module import-light.
    """
    Evaluation, EvaluationPoint, Vintage, VintagePoint, Result, Attempt, Task, Execution, Actual, Revision, Dataset, Key, User, Company = models
    execution_ids=[ids.execution_id]; vintage_ids=[value for value, in session.query(Vintage.id).filter_by(company_id=ids.company_id)]
    session.query(EvaluationPoint).filter_by(evaluation_id=ids.evaluation_id).delete(synchronize_session=False)
    session.query(Evaluation).filter_by(id=ids.evaluation_id).delete(synchronize_session=False)
    session.query(VintagePoint).filter(VintagePoint.forecast_vintage_id.in_(vintage_ids)).delete(synchronize_session=False)
    session.query(Vintage).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
    session.query(Result).filter(Result.execution_id.in_(execution_ids)).delete(synchronize_session=False)
    session.query(Attempt).filter(Attempt.execution_id.in_(execution_ids)).delete(synchronize_session=False)
    session.query(Task).filter(Task.execution_id.in_(execution_ids)).delete(synchronize_session=False)
    session.query(Execution).filter(Execution.execution_id.in_(execution_ids)).delete(synchronize_session=False)
    session.query(Revision).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
    session.query(Actual).filter_by(company_id=ids.company_id).delete(synchronize_session=False)
    session.query(Dataset).filter_by(id=ids.dataset_id).delete(synchronize_session=False)
    session.query(Key).filter_by(user_id=ids.user_id).delete(synchronize_session=False)
    session.query(User).filter_by(id=ids.user_id).delete(synchronize_session=False)
    session.query(Company).filter_by(id=ids.company_id).delete(synchronize_session=False)
    session.commit()
