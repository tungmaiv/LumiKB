"""Knowledge Base model."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, model_repr

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.draft import Draft
    from app.models.permission import KBPermission
    from app.models.user import User


class KnowledgeBase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Knowledge Base model for organizing documents.

    Columns:
    - id: UUID primary key
    - name: VARCHAR(255), required
    - description: TEXT, optional
    - owner_id: UUID FK to users
    - status: VARCHAR(20), default 'active'
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ
    """

    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="active",
        nullable=False,
    )
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        server_default="{}",
        nullable=False,
    )

    # Relationships
    owner: Mapped["User | None"] = relationship(
        "User", back_populates="knowledge_bases"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
    drafts: Mapped[list["Draft"]] = relationship(
        "Draft",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
    permissions: Mapped[list["KBPermission"]] = relationship(
        "KBPermission",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return model_repr(self, "id", "name", "status")
