"""User model compatible with FastAPI-Users."""

from datetime import datetime
from typing import TYPE_CHECKING

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, model_repr

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.permission import KBPermission


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model extending FastAPI-Users base with timestamps.

    Columns from SQLAlchemyBaseUserTableUUID:
    - id: UUID primary key
    - email: str, unique, indexed
    - hashed_password: str
    - is_active: bool, default True
    - is_superuser: bool, default False
    - is_verified: bool, default False

    Additional columns:
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ
    """

    __tablename__ = "users"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        "KnowledgeBase",
        back_populates="owner",
    )
    kb_permissions: Mapped[list["KBPermission"]] = relationship(
        "KBPermission",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return model_repr(self, "id", "email", "is_active")
