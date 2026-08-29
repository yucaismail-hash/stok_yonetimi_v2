import asyncio
import json
import os
import unittest
from unittest.mock import patch

from app.api.v2.endpoints.health import health_check
from app.config.production_safety import (
    ProductionConfigurationError,
    validate_backend_production_configuration,
)
from app.services.security.encryption_service import EncryptionService
from app.workers.business_workflow import WorkerSettings


VALID_JWT = "synthetic-production-jwt-secret"
VALID_MASTER = "synthetic-production-master-key"


class _HealthyDb:
    def execute(self, _statement):
        return None


class _UnavailableDb:
    def execute(self, _statement):
        raise RuntimeError("postgresql://not-for-response")


class ProductionSafetyTests(unittest.TestCase):
    def _production(self, **overrides):
        values = {"DATABASE_ENVIRONMENT": "production", **overrides}
        return patch.dict(os.environ, values, clear=True)

    def test_production_rejects_missing_or_default_jwt_secret(self):
        with self._production(STOKONOMI_MASTER_KEY=VALID_MASTER):
            with self.assertRaisesRegex(ProductionConfigurationError, "SECRET_KEY"):
                validate_backend_production_configuration()
        with self._production(SECRET_KEY="your-secret-key", STOKONOMI_MASTER_KEY=VALID_MASTER):
            with self.assertRaisesRegex(ProductionConfigurationError, "SECRET_KEY"):
                validate_backend_production_configuration()

    def test_production_accepts_explicit_jwt_and_master_key(self):
        with self._production(SECRET_KEY=VALID_JWT, STOKONOMI_MASTER_KEY=VALID_MASTER):
            validate_backend_production_configuration()

    def test_production_rejects_missing_or_default_master_key(self):
        with self._production(SECRET_KEY=VALID_JWT):
            with self.assertRaisesRegex(ProductionConfigurationError, "STOKONOMI_MASTER_KEY"):
                validate_backend_production_configuration()
        with self._production(SECRET_KEY=VALID_JWT, STOKONOMI_MASTER_KEY="dev-master-key-32-bytes-long!!"):
            with self.assertRaisesRegex(ProductionConfigurationError, "STOKONOMI_MASTER_KEY"):
                validate_backend_production_configuration()

    def test_encryption_and_worker_fail_before_production_work_with_unsafe_key(self):
        with self._production(SECRET_KEY=VALID_JWT):
            with self.assertRaisesRegex(ProductionConfigurationError, "STOKONOMI_MASTER_KEY"):
                EncryptionService(object())
            with self.assertRaisesRegex(ProductionConfigurationError, "STOKONOMI_MASTER_KEY"):
                WorkerSettings.from_env()

    def test_development_fallback_remains_supported(self):
        with patch.dict(os.environ, {"DATABASE_ENVIRONMENT": "development"}, clear=True):
            self.assertEqual(EncryptionService(object()).master_key, b"dev-master-key-32-bytes-long!!")
            self.assertEqual(WorkerSettings.from_env().poll_seconds, 5)

    def test_health_uses_200_only_when_database_is_available(self):
        healthy = asyncio.run(health_check(_HealthyDb()))
        self.assertEqual(healthy["status"], "ok")
        unavailable = asyncio.run(health_check(_UnavailableDb()))
        self.assertEqual(unavailable.status_code, 503)
        body = json.loads(unavailable.body)
        self.assertEqual(body["database"], "unavailable")
        self.assertNotIn("postgresql", unavailable.body.decode())

    def test_dockerfile_uses_runtime_port_expansion_without_default_secrets(self):
        with open("Dockerfile", encoding="utf-8") as dockerfile:
            content = dockerfile.read()
        self.assertIn("${PORT:-8000}", content)
        self.assertNotIn("ENV SECRET_KEY", content)
        self.assertNotIn("ENV DATABASE_URL", content)


if __name__ == "__main__":
    unittest.main()
