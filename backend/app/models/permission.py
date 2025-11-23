"""Knowledge Base Permission model."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, model_repr

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.user import User


class PermissionLevel(str, enum.Enum):
    """Permission levels for Knowledge Base access."""

    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class KBPermission(Base):
    """Knowledge Base Permission model.

    Columns:
    - id: UUID primary key
    - user_id: UUID FK to users (CASCADE delete)
    - kb_id: UUID FK to knowledge_bases (CASCADE delete)
    - permission_level: ENUM (READ, WRITE, ADMIN)
    - created_at: TIMESTAMPTZ

    Constraints:
    - Unique on (user_id, kb_id)
    """

    __tablename__ = "kb_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "kb_id", name="uq_kb_permissions_user_kb"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    kb_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_level: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel, name="permission_level", create_constraint=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="kb_permissions")
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase",
        back_populates="permissions",
    )

    def __repr__(self) -> str:
        return model_repr(self, "id", "user_id", "kb_id", "permission_level")
