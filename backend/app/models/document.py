"""Document model."""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, model_repr

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase


class DocumentStatus(str, enum.Enum):
    """Document processing status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Document model for files in a Knowledge Base.

    Columns:
    - id: UUID primary key
    - kb_id: UUID FK to knowledge_bases (CASCADE delete)
    - name: VARCHAR(255), required
    - file_path: VARCHAR(500), optional
    - status: ENUM (PENDING, PROCESSING, READY, FAILED, ARCHIVED)
    - chunk_count: INTEGER, default 0
    - last_error: TEXT, optional
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ
    """

    __tablename__ = "documents"

    kb_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", create_constraint=True),
        server_default="PENDING",
        nullable=False,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        nullable=False,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase",
        back_populates="documents",
    )

    def __repr__(self) -> str:
        return model_repr(self, "id", "name", "status")
