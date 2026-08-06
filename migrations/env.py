"""Alembic environment guarded by ADR-033."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None
_KNOWN_ENVIRONMENTS = {"local", "test", "development", "staging", "production"}


def _require_migration_environment() -> str:
    environment = os.getenv("DATABASE_ENVIRONMENT", "").strip().lower()
    if environment not in _KNOWN_ENVIRONMENTS:
        raise RuntimeError("DATABASE_ENVIRONMENT must be explicitly configured for Alembic")
    if environment == "production" and os.getenv("ALLOW_PRODUCTION_MIGRATION", "").lower() != "true":
        raise RuntimeError("ALLOW_PRODUCTION_MIGRATION=true is required for production migrations")
    return environment


def run_migrations_offline() -> None:
    _require_migration_environment()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for Alembic")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _require_migration_environment()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for Alembic")
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="public",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
