from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.runtime import RuntimeCheckpoint, RuntimeExecution, RuntimeResultReference, RuntimeTask, RuntimeTaskAttempt


def _checks(model):
    return {constraint.name: str(constraint.sqltext) for constraint in model.__table__.constraints if constraint.__class__.__name__ == "CheckConstraint"}


def test_runtime_models_use_direct_base_and_uuidv7_defaults():
    assert RuntimeExecution.__base__ is Base
    for model, key in ((RuntimeExecution, "execution_id"), (RuntimeTask, "id"), (RuntimeTaskAttempt, "id"), (RuntimeCheckpoint, "id"), (RuntimeResultReference, "id")):
        column = model.__table__.c[key]
        assert isinstance(column.type, UUID)
        assert column.default.arg.__module__ == "uuid_extensions.uuid7"


def test_runtime_metadata_has_jsonb_timezone_and_constraints():
    assert isinstance(RuntimeExecution.__table__.c.metadata.type, JSONB)
    assert RuntimeExecution.__table__.c.created_at.type.timezone is True
    assert RuntimeTask.__table__.c.updated_at.type.timezone is True
    assert RuntimeTaskAttempt.__table__.c.duration_ms.type.precision == 14
    assert {"ck_runtime_executions_intent_xor", "ck_runtime_executions_progress_range", "ck_runtime_executions_row_version"} <= _checks(RuntimeExecution).keys()
    assert {"ck_runtime_tasks_attempt_range", "ck_runtime_tasks_timeout", "ck_runtime_attempts_duration"} <= (_checks(RuntimeTask).keys() | _checks(RuntimeTaskAttempt).keys())
    assert {"ck_runtime_results_storage_xor", "ck_runtime_results_storage_kind"} <= _checks(RuntimeResultReference).keys()


def test_runtime_fk_and_result_scope_metadata():
    task_fk = next(fk for fk in RuntimeTask.__table__.foreign_key_constraints if fk.name == "fk_runtime_tasks_execution_company")
    attempt_fk = next(fk for fk in RuntimeTaskAttempt.__table__.foreign_key_constraints if fk.name == "fk_runtime_attempts_task_execution_company")
    checkpoint_task_fk = next(fk for fk in RuntimeCheckpoint.__table__.foreign_key_constraints if fk.elements[0].parent.name == "runtime_task_id")
    assert len(task_fk.elements) == 2
    assert len(attempt_fk.elements) == 3
    assert checkpoint_task_fk.ondelete == "SET NULL"
    indexes = {index.name for index in RuntimeResultReference.__table__.indexes}
    assert {"uq_runtime_results_execution_scope", "uq_runtime_results_task_scope"} <= indexes
