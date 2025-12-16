"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import litellm
import structlog
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.chat_stream import router as chat_stream_router
from app.api.v1.documents import router as documents_router
from app.api.v1.drafts import router as drafts_router
from app.api.v1.generate import router as generate_router
from app.api.v1.generate_stream import router as generate_stream_router
from app.api.v1.groups import router as groups_router
from app.api.v1.health import liveness_check, readiness_check
from app.api.v1.health import router as health_router
from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.metrics import create_instrumentator, metrics_endpoint
from app.api.v1.models import admin_router as models_admin_router
from app.api.v1.models import public_router as models_public_router
from app.api.v1.observability import router as observability_router
from app.api.v1.search import router as search_router
from app.api.v1.users import router as users_router
from app.core.auth import refresh_session_timeout_cache
from app.core.config import settings
from app.core.database import get_async_session
from app.core.logging import configure_logging
from app.core.redis import RedisClient
from app.integrations.litellm_callback import observability_callback
from app.integrations.litellm_client import close_litellm_clients
from app.integrations.qdrant_client import qdrant_service
from app.middleware import RequestContextMiddleware
from app.services.litellm_proxy_service import sync_all_models_to_proxy
from app.services.model_registry_service import ModelRegistryService

# Configure structured logging at module load
configure_logging(
    json_logs=not settings.debug, log_level="DEBUG" if settings.debug else "INFO"
)


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events.

    Manages:
    - Redis connection lifecycle
    - Qdrant client lifecycle
    - LiteLLM async client lifecycle
    - LiteLLM observability callback registration (Story 9-6)
    - Session timeout cache initialization
    - LLM model sync to LiteLLM proxy
    """
    # Startup: Initialize Redis connection
    await RedisClient.get_client()
    # Startup: Prime session timeout cache from DB config
    await refresh_session_timeout_cache()

    # Startup: Register LiteLLM observability callback (Story 9-6)
    # This automatically traces all LLM calls (embeddings, completions) without
    # manual instrumentation at each call site
    litellm.callbacks.append(observability_callback)
    logger.info("litellm_observability_callback_registered")

    # Startup: Sync DB models to LiteLLM proxy (Option C implementation)
    # This ensures models registered in Admin UI work for connection tests
    # even after proxy container restarts
    try:
        async for session in get_async_session():
            service = ModelRegistryService(session)
            models = await service.get_all_active_models()
            if models:
                results = await sync_all_models_to_proxy(
                    models, service.get_decrypted_api_key
                )
                logger.info(
                    "startup_model_sync_completed",
                    total=results["total"],
                    success=results["success"],
                    failed=results["failed"],
                )
            break  # Only need one iteration
    except Exception as e:
        # Non-fatal - models will sync on next create/update
        logger.warning(
            "startup_model_sync_failed",
            error=str(e),
            hint="Models will sync when created/updated via Admin UI",
        )

    yield
    # Shutdown: Close connections gracefully (order matters)
    # 1. Close LiteLLM first - must happen while event loop is running
    #    This prevents "no event loop in thread" errors from atexit handlers
    await close_litellm_clients()
    # 2. Close Redis
    await RedisClient.close()
    # 3. Close Qdrant client with grace period to allow pending requests
    qdrant_service.close(grpc_grace=2.0)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise RAG-powered knowledge management platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request context middleware for logging correlation
app.add_middleware(RequestContextMiddleware)

# Prometheus instrumentation (Story 7.5: AC-7.5.1)
# Must be added after middleware to capture all requests
instrumentator = create_instrumentator()
instrumentator.instrument(app)

# Metrics endpoint (exposed at /metrics for Prometheus scraping)
app.add_api_route(
    "/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False
)

# Include API v1 routers
app.include_router(admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(chat_stream_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(drafts_router, prefix="/api/v1")
app.include_router(generate_router, prefix="/api/v1")
app.include_router(generate_stream_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(models_admin_router, prefix="/api/v1")
app.include_router(models_public_router, prefix="/api/v1")
app.include_router(observability_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint (legacy)."""
    return {"status": "healthy", "version": settings.app_version}


# Root-level health endpoints for orchestration probes (Story 7.4: AC-7.4.4)
# These are mounted at / for Docker/Kubernetes health checks


@app.get("/health")
async def root_health():
    """Liveness probe at root level for Docker/K8s orchestration."""
    return await liveness_check()


@app.get("/ready")
async def root_ready(response: Response):
    """Readiness probe at root level for Docker/K8s orchestration."""
    return await readiness_check(response)


@app.get("/api/v1/")
async def root() -> dict[str, str]:
    """API root endpoint."""
    return {"message": f"Welcome to {settings.app_name} API"}
