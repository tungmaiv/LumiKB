"""API v1 routers."""

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.users import router as users_router

__all__ = ["admin_router", "auth_router", "kb_router", "users_router"]
