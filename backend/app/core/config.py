"""Application configuration using pydantic-settings.

Story 7.4: Production Deployment Configuration
- All secrets loaded from environment variables
- Validation fails fast if required secrets missing in production
"""

import sys

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    In production (LUMIKB_ENVIRONMENT=production), the application will
    fail to start if insecure default values are detected for:
    - secret_key
    - jwt_secret (if set)
    - database passwords
    - API keys
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LUMIKB_",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "LumiKB"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (PostgreSQL)
    database_url: str = (
        "postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO (S3-Compatible Object Storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "lumikb"
    minio_secret_key: str = "lumikb_dev_password"
    minio_bucket: str = "lumikb-documents"
    minio_secure: bool = False

    # Qdrant (Vector Database)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_collection: str = "lumikb_documents"

    # LiteLLM (LLM Gateway)
    litellm_url: str = "http://localhost:4000"
    litellm_api_key: str = "sk-dev-master-key"

    # Ollama (Local LLM Server)
    # Direct connection URL for Ollama when testing models outside of LiteLLM proxy
    ollama_url: str = "http://localhost:11434"

    # Ollama URL for LiteLLM proxy registration (Option C: DB-to-Proxy Sync)
    # When backend runs on host but LiteLLM proxy runs in Docker, the proxy
    # needs to use host.docker.internal to reach Ollama on the host.
    # This URL is used when registering Ollama models with the proxy.
    ollama_url_for_proxy: str = "http://host.docker.internal:11434"

    # Security
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # Encryption key for API keys (Fernet, base64-encoded 32-byte key)
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = "ZGV2LWVuY3J5cHRpb24ta2V5LWNoYW5nZS1tZQ=="  # Base64 dev key

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    document_processing_timeout: int = 600  # 10 minutes visibility timeout
    max_parsing_retries: int = 3

    # Embedding Configuration
    # Use explicit Ollama model name (768 dimensions, same as Gemini)
    embedding_model: str = "ollama-embedding"
    embedding_batch_size: int = 20
    embedding_max_retries: int = 5
    embedding_timeout: int = 30  # seconds per batch

    # LLM Configuration (for answer synthesis)
    # Use ollama/model format - LiteLLM routes this directly to Ollama
    # llama3.2 is preferred as it loads quickly and responds well
    llm_model: str = "ollama/llama3.2"
    llm_timeout: int = 120  # seconds for LLM completion (longer than embedding)

    # Chunking Configuration
    chunk_size: int = 500  # target tokens
    chunk_overlap: int = 50  # overlap tokens (10%)

    # LangFuse Observability (Story 9-11)
    # Optional external observability provider for LLM tracing
    langfuse_enabled: bool = False
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_flush_timeout_seconds: int = 5  # Timeout for flush operations

    # Observability Retention (Story 9-14)
    # Days to retain data before cleanup
    observability_retention_days: int = 90  # traces, spans, document_events
    observability_metrics_retention_days: int = 365  # metrics_aggregates
    observability_sync_status_retention_days: int = 7  # provider_sync_status

    # Parser Configuration (Story 7-32: Docling Integration)
    # System-level feature flag to enable Docling parser
    # When False, KB-level parser_backend settings are ignored and Unstructured is always used
    parser_docling_enabled: bool = False

    # Document Lifecycle Configuration (Epic 6)
    bulk_purge_max_batch_size: int = 100  # Max documents per bulk purge request
    archive_grace_period_days: int = (
        0  # Days after archive before purge allowed (0 = immediate)
    )

    # Environment (Story 7.4: Production Deployment)
    environment: str = "development"  # 'development', 'staging', 'production'

    # Insecure default values that must be changed in production
    _INSECURE_DEFAULTS = {
        "secret_key": ["change-me-in-production", "secret", "changeme"],
        "litellm_api_key": ["sk-dev-master-key"],
    }

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Validate that insecure defaults are not used in production.

        Story 7.4 AC-7.4.3: All secrets loaded from environment variables.
        Fails fast if production environment uses insecure default values.
        """
        if self.environment.lower() != "production":
            return self

        errors: list[str] = []

        # Check for insecure default values
        for field_name, insecure_values in self._INSECURE_DEFAULTS.items():
            value = getattr(self, field_name, None)
            if value and value.lower() in [v.lower() for v in insecure_values]:
                errors.append(
                    f"LUMIKB_{field_name.upper()} has insecure default value in production"
                )

        # Check database URL for default password
        if "lumikb_dev_password" in self.database_url.lower():
            errors.append("LUMIKB_DATABASE_URL contains default development password")

        # Check MinIO credentials
        if self.minio_secret_key == "lumikb_dev_password":
            errors.append("LUMIKB_MINIO_SECRET_KEY has default development password")

        if errors:
            error_msg = (
                "\n\nPRODUCTION SECRETS VALIDATION FAILED\n"
                "====================================\n"
                "The following security issues must be resolved:\n\n"
                + "\n".join(f"  - {e}" for e in errors)
                + "\n\nSet secure values in your .env.prod file.\n"
                "See infrastructure/.env.prod.template for guidance.\n"
            )
            print(error_msg, file=sys.stderr)
            raise ValueError(
                f"Production secrets validation failed. Issues: {', '.join(errors)}"
            )

        return self


settings = Settings()
