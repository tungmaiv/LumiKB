"""Draft model for generated documents."""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, model_repr

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.user import User


class DraftStatus(str, enum.Enum):
    """Draft lifecycle status."""

    STREAMING = "streaming"  # Generation in progress via SSE
    PARTIAL = "partial"  # Incomplete generation (user cancelled)
    COMPLETE = "complete"  # Generation finished, ready for editing
    EDITING = "editing"  # User has edited content
    EXPORTED = "exported"  # Exported to DOCX/PDF


class Draft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Draft model for AI-generated documents with citations.

    State Machine:
    - streaming → partial (on cancel) OR complete (on finish)
    - complete → editing (on first edit)
    - editing → editing (on save)
    - editing → exported (on export)

    Columns:
    - id: UUID primary key
    - kb_id: UUID FK to knowledge_bases (CASCADE delete)
    - user_id: UUID FK to users (SET NULL)
    - title: VARCHAR(500), draft title/subject
    - content: TEXT, markdown content with [n] citation markers
    - citations: JSONB, array of citation objects
    - template_type: VARCHAR(100), template used (rfp_response, checklist, etc.)
    - status: ENUM (streaming, partial, complete, editing, exported)
    - word_count: INTEGER, calculated word count
    - edit_history: JSONB, optional undo/redo snapshots
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ (for optimistic locking)
    """

    __tablename__ = "drafts"

    kb_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    citations: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    template_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[DraftStatus] = mapped_column(
        Enum(
            DraftStatus,
            name="draft_status",
            create_type=False,
            values_callable=lambda x: [m.value for m in x],  # Use lowercase values
        ),
        server_default="streaming",
        nullable=False,
    )
    word_count: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        nullable=False,
    )
    edit_history: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase", back_populates="drafts"
    )
    user: Mapped["User | None"] = relationship("User", back_populates="drafts")

    def __repr__(self) -> str:
        """String representation."""
        return model_repr(self, "id", "title", "status", "kb_id")
