"""Outbox model for transactional event processing."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, model_repr


class Outbox(Base):
    """Outbox model for transactional consistency.

    Used for reliable event processing with at-least-once delivery.

    Columns:
    - id: UUID primary key
    - event_type: VARCHAR(50), required
    - aggregate_id: UUID, required
    - payload: JSONB, required
    - created_at: TIMESTAMPTZ
    - processed_at: TIMESTAMPTZ, nullable (NULL = unprocessed)
    - attempts: INTEGER, default 0
    - last_error: TEXT, optional
    """

    __tablename__ = "outbox"
    __table_args__ = (
        # Index for finding unprocessed events efficiently
        Index(
            "idx_outbox_unprocessed",
            "created_at",
            postgresql_where="processed_at IS NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        nullable=False,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return model_repr(self, "id", "event_type", "aggregate_id", "processed_at")
