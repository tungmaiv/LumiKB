"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

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

    # Security
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
