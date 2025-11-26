"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.search import router as search_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.redis import RedisClient
from app.integrations.litellm_client import close_litellm_clients
from app.integrations.qdrant_client import qdrant_service
from app.middleware import RequestContextMiddleware

# Configure structured logging at module load
configure_logging(
    json_logs=not settings.debug, log_level="DEBUG" if settings.debug else "INFO"
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events.

    Manages:
    - Redis connection lifecycle
    - Qdrant client lifecycle
    - LiteLLM async client lifecycle
    """
    # Startup: Initialize Redis connection
    await RedisClient.get_client()
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

# Include API v1 routers
app.include_router(admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/api/v1/")
async def root() -> dict[str, str]:
    """API root endpoint."""
    return {"message": f"Welcome to {settings.app_name} API"}
