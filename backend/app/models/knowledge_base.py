"""Knowledge Base model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, model_repr

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.draft import Draft
    from app.models.kb_group_permission import KBGroupPermission
    from app.models.llm_model import LLMModel
    from app.models.permission import KBPermission
    from app.models.user import User


class KnowledgeBase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Knowledge Base model for organizing documents.

    Columns:
    - id: UUID primary key
    - name: VARCHAR(255), required
    - description: TEXT, optional
    - tags: JSONB array of strings for categorization and search
    - owner_id: UUID FK to users
    - status: VARCHAR(20), default 'active'
    - embedding_model_id: UUID FK to llm_models (embedding type)
    - generation_model_id: UUID FK to llm_models (generation type)
    - qdrant_collection_name: VARCHAR(100), collection name in Qdrant
    - qdrant_vector_size: INTEGER, vector dimensions for this KB
    - similarity_threshold: FLOAT, KB-level similarity threshold override
    - search_top_k: INTEGER, KB-level top_k override
    - temperature: FLOAT, KB-level generation temperature override
    - rerank_enabled: BOOLEAN, whether reranking is enabled
    - archived_at: TIMESTAMPTZ, when KB was archived (Story 7-24)
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ
    """

    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        server_default="[]",
        nullable=False,
    )
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

    # Model references (Story 7-10: KB Model Configuration)
    embedding_model_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("llm_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    generation_model_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("llm_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Qdrant collection metadata
    qdrant_collection_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    qdrant_vector_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # KB-level RAG parameter overrides
    similarity_threshold: Mapped[float | None] = mapped_column(
        Float, server_default="0.7", nullable=True
    )
    search_top_k: Mapped[int | None] = mapped_column(
        Integer, server_default="10", nullable=True
    )
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    rerank_enabled: Mapped[bool | None] = mapped_column(
        Boolean, server_default="false", nullable=True
    )

    # Archive timestamp (Story 7-24: KB Archive Backend)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    group_permissions: Mapped[list["KBGroupPermission"]] = relationship(
        "KBGroupPermission",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
    embedding_model: Mapped["LLMModel | None"] = relationship(
        "LLMModel",
        foreign_keys=[embedding_model_id],
        lazy="joined",
    )
    generation_model: Mapped["LLMModel | None"] = relationship(
        "LLMModel",
        foreign_keys=[generation_model_id],
        lazy="joined",
    )

    def __repr__(self) -> str:
        return model_repr(self, "id", "name", "status")
