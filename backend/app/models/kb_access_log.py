"""KB Access Log model for tracking user KB access patterns."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, model_repr

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.user import User


class AccessType(str, enum.Enum):
    """Types of KB access for tracking."""

    SEARCH = "search"
    VIEW = "view"
    EDIT = "edit"


class KBAccessLog(Base):
    """KB Access Log model for recommendation algorithm.

    Tracks user interactions with KBs to power personalized recommendations.
    Uses fire-and-forget pattern for minimal latency impact.

    Columns:
    - id: UUID primary key
    - user_id: UUID FK to users (CASCADE delete)
    - kb_id: UUID FK to knowledge_bases (CASCADE delete)
    - accessed_at: TIMESTAMPTZ, default NOW()
    - access_type: ENUM (search, view, edit)

    Indexes:
    - idx_kb_access_user_kb_date: (user_id, kb_id, accessed_at DESC)
    """

    __tablename__ = "kb_access_log"
    __table_args__ = (
        Index(
            "idx_kb_access_user_kb_date",
            "user_id",
            "kb_id",
            "accessed_at",
            postgresql_ops={"accessed_at": "DESC"},
        ),
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
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    access_type: Mapped[AccessType] = mapped_column(
        Enum(
            AccessType,
            name="access_type_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase")

    def __repr__(self) -> str:
        return model_repr(self, "id", "user_id", "kb_id", "access_type")
