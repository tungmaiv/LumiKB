"""Unit tests for production secrets validation.

Story 7.4: Production Deployment Configuration
AC-7.4.3: All secrets loaded from environment variables (no hardcoded credentials)

Tests cover:
- Development environment allows insecure defaults
- Production environment rejects insecure defaults
- Specific secret validations (secret_key, database_url, minio, litellm)
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestProductionSecretsValidation:
    """Tests for production secrets validation in Settings."""

    def test_development_allows_insecure_defaults(self) -> None:
        """Test that development environment allows insecure default values."""
        env = {
            "LUMIKB_ENVIRONMENT": "development",
            "LUMIKB_SECRET_KEY": "change-me-in-production",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "lumikb_dev_password",
            "LUMIKB_LITELLM_API_KEY": "sk-dev-master-key",
        }

        with patch.dict(os.environ, env, clear=False):
            # Import Settings class directly to avoid module-level instantiation
            from app.core.config import Settings

            # Should not raise any exception in development
            s = Settings()

            assert s.environment == "development"
            assert s.secret_key == "change-me-in-production"

    def test_production_rejects_insecure_secret_key(self) -> None:
        """Test that production environment rejects insecure secret_key."""
        env = {
            "LUMIKB_ENVIRONMENT": "production",
            "LUMIKB_SECRET_KEY": "change-me-in-production",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:secure_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "secure_minio_password",
            "LUMIKB_LITELLM_API_KEY": "sk-secure-production-key-123",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings()

            # Check the error message contains relevant information
            error_str = str(exc_info.value)
            assert "SECRET_KEY" in error_str
            assert "insecure" in error_str.lower()

    def test_production_rejects_default_database_password(self) -> None:
        """Test that production environment rejects default database password."""
        env = {
            "LUMIKB_ENVIRONMENT": "production",
            "LUMIKB_SECRET_KEY": "secure-production-secret-key-32chars",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "secure_minio_password",
            "LUMIKB_LITELLM_API_KEY": "sk-secure-production-key-123",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings()

            error_str = str(exc_info.value)
            assert "DATABASE_URL" in error_str

    def test_production_rejects_default_minio_password(self) -> None:
        """Test that production environment rejects default MinIO password."""
        env = {
            "LUMIKB_ENVIRONMENT": "production",
            "LUMIKB_SECRET_KEY": "secure-production-secret-key-32chars",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:secure_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "lumikb_dev_password",
            "LUMIKB_LITELLM_API_KEY": "sk-secure-production-key-123",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings()

            error_str = str(exc_info.value)
            assert "MINIO_SECRET_KEY" in error_str

    def test_production_rejects_default_litellm_key(self) -> None:
        """Test that production environment rejects default LiteLLM API key."""
        env = {
            "LUMIKB_ENVIRONMENT": "production",
            "LUMIKB_SECRET_KEY": "secure-production-secret-key-32chars",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:secure_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "secure_minio_password",
            "LUMIKB_LITELLM_API_KEY": "sk-dev-master-key",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings()

            error_str = str(exc_info.value)
            assert "LITELLM_API_KEY" in error_str

    def test_production_allows_secure_configuration(self) -> None:
        """Test that production environment accepts secure configuration."""
        env = {
            "LUMIKB_ENVIRONMENT": "production",
            "LUMIKB_SECRET_KEY": "secure-production-secret-key-with-at-least-32-characters",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:secure_db_password_12345@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "secure_minio_password_12345",
            "LUMIKB_LITELLM_API_KEY": "sk-secure-production-key-abcd1234",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            # Should not raise any exception with secure values
            s = Settings()

            assert s.environment == "production"
            assert "secure" in s.secret_key

    def test_staging_environment_allows_insecure_defaults(self) -> None:
        """Test that staging environment allows insecure defaults (only production validates)."""
        env = {
            "LUMIKB_ENVIRONMENT": "staging",
            "LUMIKB_SECRET_KEY": "change-me-in-production",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "lumikb_dev_password",
            "LUMIKB_LITELLM_API_KEY": "sk-dev-master-key",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            # Should not raise any exception in staging
            s = Settings()

            assert s.environment == "staging"

    def test_production_multiple_insecure_values_reports_all(self) -> None:
        """Test that all insecure values are reported when multiple exist."""
        env = {
            "LUMIKB_ENVIRONMENT": "production",
            "LUMIKB_SECRET_KEY": "change-me-in-production",
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "lumikb_dev_password",
            "LUMIKB_LITELLM_API_KEY": "sk-dev-master-key",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings()

            error_message = str(exc_info.value)
            # All issues should be mentioned
            assert "SECRET_KEY" in error_message
            assert "DATABASE_URL" in error_message
            assert "MINIO_SECRET_KEY" in error_message
            assert "LITELLM_API_KEY" in error_message


class TestEnvironmentVariableLoading:
    """Tests for environment variable loading with LUMIKB_ prefix."""

    def test_env_prefix_is_lumikb(self) -> None:
        """Test that environment variables use LUMIKB_ prefix."""
        env = {
            "LUMIKB_ENVIRONMENT": "development",
            "LUMIKB_HOST": "127.0.0.1",
            "LUMIKB_PORT": "9000",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            s = Settings()

            assert s.host == "127.0.0.1"
            assert s.port == 9000

    def test_env_without_prefix_is_ignored(self) -> None:
        """Test that environment variables without LUMIKB_ prefix are ignored."""
        env = {
            "LUMIKB_ENVIRONMENT": "development",
            "HOST": "ignored.host.com",  # No LUMIKB_ prefix
            "PORT": "12345",  # No LUMIKB_ prefix
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            s = Settings()

            # Should use defaults, not the unprefixed env vars
            assert s.host == "0.0.0.0"
            assert s.port == 8000


class TestInsecureDefaultsList:
    """Tests for the INSECURE_DEFAULTS configuration."""

    def test_secret_key_variants_are_blocked(self) -> None:
        """Test that various insecure secret_key values are blocked."""
        insecure_values = ["change-me-in-production", "secret", "changeme"]

        for insecure_value in insecure_values:
            env = {
                "LUMIKB_ENVIRONMENT": "production",
                "LUMIKB_SECRET_KEY": insecure_value,
                "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:secure_password@localhost:5432/lumikb",
                "LUMIKB_MINIO_SECRET_KEY": "secure_minio_password",
                "LUMIKB_LITELLM_API_KEY": "sk-secure-production-key-123",
            }

            with patch.dict(os.environ, env, clear=False):
                from app.core.config import Settings

                with pytest.raises(ValidationError) as exc_info:
                    Settings()

                assert "SECRET_KEY" in str(
                    exc_info.value
                ), f"Failed for value: {insecure_value}"

    def test_case_insensitive_insecure_detection(self) -> None:
        """Test that insecure value detection is case-insensitive."""
        env = {
            "LUMIKB_ENVIRONMENT": "production",
            "LUMIKB_SECRET_KEY": "CHANGE-ME-IN-PRODUCTION",  # Uppercase
            "LUMIKB_DATABASE_URL": "postgresql+asyncpg://lumikb:secure_password@localhost:5432/lumikb",
            "LUMIKB_MINIO_SECRET_KEY": "secure_minio_password",
            "LUMIKB_LITELLM_API_KEY": "sk-secure-production-key-123",
        }

        with patch.dict(os.environ, env, clear=False):
            from app.core.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "SECRET_KEY" in str(exc_info.value)
