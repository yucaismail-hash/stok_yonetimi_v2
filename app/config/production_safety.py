"""Small, fail-closed production configuration checks.

Development and test environments deliberately retain their existing local
defaults.  Production must supply its own authentication and encryption
material before either the API or the workflow worker can operate.
"""

from __future__ import annotations

import os


class ProductionConfigurationError(RuntimeError):
    """Configuration is unsafe for production use; never contains a secret."""


_PRODUCTION = "production"
_DEFAULT_JWT_SECRETS = frozenset({"your-secret-key", "docker_secret_key_123456", "prod_secret_key_123456"})
_DEFAULT_MASTER_KEYS = frozenset({"dev-master-key-32-bytes-long!!"})


def is_production_environment() -> bool:
    return os.getenv("DATABASE_ENVIRONMENT", "").strip().lower() == _PRODUCTION


def _require_configured_secret(name: str, disallowed: frozenset[str]) -> str:
    value = os.getenv(name, "").strip()
    if not value or value in disallowed:
        raise ProductionConfigurationError(f"{name} must be explicitly configured for production")
    return value


def require_production_master_key() -> str:
    """Return a production-safe master key or fail before encrypted data is used."""
    if not is_production_environment():
        return os.getenv("STOKONOMI_MASTER_KEY", "").strip()
    return _require_configured_secret("STOKONOMI_MASTER_KEY", _DEFAULT_MASTER_KEYS)


def validate_backend_production_configuration() -> None:
    """Validate only the production secrets needed before the API serves traffic."""
    if not is_production_environment():
        return
    _require_configured_secret("SECRET_KEY", _DEFAULT_JWT_SECRETS)
    require_production_master_key()


def validate_worker_production_configuration() -> None:
    """Validate the production key material needed before worker polling starts."""
    if not is_production_environment():
        return
    require_production_master_key()
