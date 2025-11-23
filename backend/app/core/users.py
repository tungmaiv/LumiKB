"""FastAPI-Users database adapter and dependencies."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, UUID], None]:
    """FastAPI dependency for user database adapter.

    Yields:
        SQLAlchemyUserDatabase: FastAPI-Users database adapter.
    """
    yield SQLAlchemyUserDatabase(session, User)
