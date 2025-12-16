"""Knowledge Base Group Permission model.

Story 5.20: Role & KB Permission Management UI (AC-5.20.5)
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, model_repr
from app.models.permission import PermissionLevel

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.knowledge_base import KnowledgeBase


class KBGroupPermission(Base):
    """Knowledge Base Group Permission model.

    Allows groups to have permissions on knowledge bases.

    Columns:
    - id: UUID primary key
    - group_id: UUID FK to groups (CASCADE delete)
    - kb_id: UUID FK to knowledge_bases (CASCADE delete)
    - permission_level: ENUM (READ, WRITE, ADMIN)
    - created_at: TIMESTAMPTZ

    Constraints:
    - Unique on (group_id, kb_id)
    """

    __tablename__ = "kb_group_permissions"
    __table_args__ = (
        UniqueConstraint("group_id", "kb_id", name="uq_kb_group_permissions_group_kb"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kb_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_level: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel, name="permission_level", create_constraint=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="kb_permissions")
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase",
        back_populates="group_permissions",
    )

    def __repr__(self) -> str:
        return model_repr(self, "id", "group_id", "kb_id", "permission_level")
