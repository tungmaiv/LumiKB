"""Group and UserGroup models for user group management.

Story 5.19: Group Management (AC-5.19.1)
Story 7.11: Navigation Restructure with RBAC Default Groups
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, model_repr

if TYPE_CHECKING:
    from app.models.kb_group_permission import KBGroupPermission
    from app.models.user import User


class Group(Base):
    """Group model for organizing users.

    Columns:
    - id: UUID primary key
    - name: VARCHAR(255), unique, NOT NULL
    - description: TEXT, nullable
    - is_active: BOOLEAN, default True (soft delete flag)
    - permission_level: INTEGER, 1-3 (User=1, Operator=2, Administrator=3)
    - is_system: BOOLEAN, default False (protects system groups from deletion)
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ
    """

    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
        nullable=False,
        index=True,
    )
    permission_level: Mapped[int] = mapped_column(
        Integer,
        server_default="1",
        nullable=False,
        index=True,
        comment="Permission tier: 1=User, 2=Operator, 3=Administrator",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        nullable=False,
        comment="System groups cannot be deleted",
    )
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

    # Relationships
    user_groups: Mapped[list["UserGroup"]] = relationship(
        "UserGroup",
        back_populates="group",
        cascade="all, delete-orphan",
    )
    kb_permissions: Mapped[list["KBGroupPermission"]] = relationship(
        "KBGroupPermission",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    @property
    def members(self) -> list["User"]:
        """Get list of users in this group."""
        return [ug.user for ug in self.user_groups]

    @property
    def member_count(self) -> int:
        """Get count of members in this group."""
        return len(self.user_groups)

    def __repr__(self) -> str:
        return model_repr(self, "id", "name", "is_active")


class UserGroup(Base):
    """Junction table for user-group membership.

    Columns:
    - user_id: UUID FK to users.id (ON DELETE CASCADE)
    - group_id: UUID FK to groups.id (ON DELETE CASCADE)
    - created_at: TIMESTAMPTZ
    - Primary key: (user_id, group_id)
    """

    __tablename__ = "user_groups"
    __table_args__ = (Index("idx_user_groups_group_id", "group_id"),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_groups",
    )
    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="user_groups",
    )

    def __repr__(self) -> str:
        return model_repr(self, "user_id", "group_id")
