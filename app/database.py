# app/database.py
from dataclasses import dataclass
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(
    DATABASE_URL,
    pool_size=8,
    max_overflow=16,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"connect_timeout": 10, "sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _legacy_init_db():
    """
    Veritabanı tablolarını oluşturur.
    Migration'lar admin endpoint'leri ile yapılır.
    """
    from app import models
    
    logger.info("📌 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("🎉 Database tables created successfully!")


_KNOWN_ENVIRONMENTS = {"local", "test", "development", "staging", "production"}


class SchemaReadinessError(RuntimeError):
    """Raised when a database cannot safely serve the configured application."""


@dataclass(frozen=True)
class SchemaReadiness:
    status: str
    current_revision: str | None = None
    expected_revision: str | None = None


def classify_database_environment(value: str | None = None) -> str:
    environment = (value if value is not None else os.getenv("DATABASE_ENVIRONMENT", "")).strip().lower()
    return environment if environment in _KNOWN_ENVIRONMENTS else "unknown"


def is_managed_database(database_url: str = DATABASE_URL) -> bool:
    return database_url.startswith("postgresql")


def _expected_revision() -> str | None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    return ScriptDirectory.from_config(config).get_current_head()


def verify_schema_readiness(bind=None) -> SchemaReadiness:
    """Read managed schema history without creating or changing database objects."""
    if not is_managed_database():
        return SchemaReadiness(status="bootstrap_allowed")
    expected_revision = _expected_revision()
    connection = bind.connect() if bind is not None else engine.connect()
    try:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        exists = connection.execute(text("SELECT to_regclass('public.alembic_version')")).scalar()
        if not exists:
            return SchemaReadiness(status="unversioned", expected_revision=expected_revision)
        current_revision = connection.execute(text("SELECT version_num FROM public.alembic_version LIMIT 1")).scalar()
        if current_revision == expected_revision:
            return SchemaReadiness(status="current", current_revision=current_revision, expected_revision=expected_revision)
        return SchemaReadiness(status="behind", current_revision=current_revision, expected_revision=expected_revision)
    except Exception as exc:
        raise SchemaReadinessError("managed database schema readiness is unavailable") from exc
    finally:
        connection.rollback()
        connection.close()


def bootstrap_disposable_database() -> None:
    environment = classify_database_environment()
    bootstrap_allowed = os.getenv("ALLOW_SCHEMA_BOOTSTRAP", "").strip().lower() == "true"
    if environment not in {"local", "test"} or not bootstrap_allowed or is_managed_database():
        raise SchemaReadinessError("disposable schema bootstrap is not authorized for this database")
    from app import models

    Base.metadata.create_all(bind=engine)


def init_db() -> SchemaReadiness:
    """Apply ADR-033 startup policy without mutating managed PostgreSQL."""
    environment = classify_database_environment()
    if environment == "unknown":
        raise SchemaReadinessError("DATABASE_ENVIRONMENT must be explicitly configured")
    if not is_managed_database():
        if os.getenv("ALLOW_SCHEMA_BOOTSTRAP", "").strip().lower() == "true":
            bootstrap_disposable_database()
            return SchemaReadiness(status="bootstrap_allowed")
        return SchemaReadiness(status="unversioned")
    readiness = verify_schema_readiness()
    if readiness.status == "current":
        return readiness
    transition_allowed = os.getenv("ALLOW_UNVERSIONED_MANAGED_SCHEMA", "").strip().lower() == "true"
    if readiness.status == "unversioned" and transition_allowed:
        logger.warning("Managed schema is unversioned; transition flag permits non-mutating startup")
        return readiness
    raise SchemaReadinessError(f"managed database schema is {readiness.status}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
