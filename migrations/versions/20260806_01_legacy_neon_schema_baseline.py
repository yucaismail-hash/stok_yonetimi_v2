"""Legacy Neon Schema Baseline.

This revision establishes future Alembic lineage only. It deliberately performs
no DDL and must never be used to recreate the historical schema. The current
ORM metadata is not asserted to match the existing live schema.
"""

from typing import Sequence, Union


revision: str = "20260806_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
