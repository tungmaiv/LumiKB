"""Audit Event model in separate audit schema."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, model_repr


class AuditEvent(Base):
    """Audit Event model for immutable audit logging.

    Stored in the 'audit' schema with INSERT-only permissions.

    Columns:
    - id: UUID primary key
    - timestamp: TIMESTAMPTZ, required
    - user_id: UUID, optional (for anonymous actions)
    - action: VARCHAR(50), required
    - resource_type: VARCHAR(50), required
    - resource_id: UUID, optional
    - details: JSONB, optional
    - ip_address: INET, optional
    """

    __tablename__ = "events"
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        {"schema": "audit"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)

    def __repr__(self) -> str:
        return model_repr(self, "id", "action", "resource_type", "timestamp")
