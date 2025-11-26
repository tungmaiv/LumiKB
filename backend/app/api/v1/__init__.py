"""API v1 routers."""

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.search import router as search_router
from app.api.v1.users import router as users_router

__all__ = [
    "admin_router",
    "auth_router",
    "documents_router",
    "health_router",
    "kb_router",
    "search_router",
    "users_router",
]
