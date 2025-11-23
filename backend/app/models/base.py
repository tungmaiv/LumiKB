"""SQLAlchemy declarative base and common model mixins."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin providing created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Mixin providing UUID primary key with PostgreSQL gen_random_uuid()."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )


def model_repr(instance: Any, *attrs: str) -> str:
    """Generate a consistent __repr__ for models.

    Args:
        instance: The model instance.
        *attrs: Attribute names to include in the repr.

    Returns:
        A string representation of the model.
    """
    class_name = instance.__class__.__name__
    attr_strs = [f"{attr}={getattr(instance, attr)!r}" for attr in attrs]
    return f"{class_name}({', '.join(attr_strs)})"
