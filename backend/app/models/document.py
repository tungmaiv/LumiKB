"""Document model."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, model_repr

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.user import User


class DocumentStatus(str, enum.Enum):
    """Document processing status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class ProcessingStep(str, enum.Enum):
    """Document processing pipeline steps."""

    UPLOAD = "upload"
    PARSE = "parse"
    CHUNK = "chunk"
    EMBED = "embed"
    INDEX = "index"
    COMPLETE = "complete"


class StepStatus(str, enum.Enum):
    """Status of individual processing steps."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Document model for files in a Knowledge Base.

    Columns:
    - id: UUID primary key
    - kb_id: UUID FK to knowledge_bases (CASCADE delete)
    - name: VARCHAR(255), display name
    - original_filename: VARCHAR(255), original uploaded filename
    - mime_type: VARCHAR(100), MIME type of the file
    - file_size_bytes: BIGINT, file size in bytes
    - file_path: VARCHAR(500), MinIO storage path
    - checksum: VARCHAR(64), SHA-256 hash
    - status: ENUM (PENDING, PROCESSING, READY, FAILED, ARCHIVED)
    - chunk_count: INTEGER, number of chunks after processing
    - processing_started_at: TIMESTAMPTZ, when processing began
    - processing_completed_at: TIMESTAMPTZ, when processing finished
    - last_error: TEXT, last error message if failed
    - retry_count: INTEGER, number of processing retries
    - uploaded_by: UUID FK to users
    - deleted_at: TIMESTAMPTZ, soft delete timestamp
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ
    """

    __tablename__ = "documents"

    kb_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
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
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        nullable=False,
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        server_default="1",
        nullable=False,
    )
    version_history: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        server_default="[]",
        nullable=True,
    )
    # Processing step tracking (Story 5-23)
    processing_steps: Mapped[dict] = mapped_column(
        JSONB,
        server_default="{}",
        nullable=False,
    )
    current_step: Mapped[str] = mapped_column(
        String(20),
        server_default="upload",
        nullable=False,
    )
    step_errors: Mapped[dict] = mapped_column(
        JSONB,
        server_default="{}",
        nullable=False,
    )
    # Document tags (Story 5-22)
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        server_default="[]",
        nullable=False,
    )

    # Relationships
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase",
        back_populates="documents",
    )
    uploader: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[uploaded_by],
    )

    def __repr__(self) -> str:
        return model_repr(self, "id", "name", "status")
