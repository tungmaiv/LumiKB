"""add_kb_access_log_table

Revision ID: 9c4424c51c68
Revises: 7279836c14d9
Create Date: 2025-12-03 11:23:25.313532

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "9c4424c51c68"
down_revision: Union[str, Sequence[str], None] = "7279836c14d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create kb_access_log table for tracking user KB access patterns.

    Used by KB recommendation algorithm (Story 5.8).
    """
    # Create kb_access_log table with enum created inline
    op.create_table(
        "kb_access_log",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "kb_id",
            UUID(as_uuid=True),
            sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "accessed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "access_type",
            postgresql.ENUM("search", "view", "edit", name="access_type_enum", create_type=True),
            nullable=False,
        ),
    )

    # Create composite index for efficient queries by user, kb, and date
    op.create_index(
        "idx_kb_access_user_kb_date",
        "kb_access_log",
        ["user_id", "kb_id", sa.text("accessed_at DESC")],
    )


def downgrade() -> None:
    """Drop kb_access_log table and access_type_enum."""
    op.drop_index("idx_kb_access_user_kb_date", table_name="kb_access_log")
    op.drop_table("kb_access_log")

    # Drop the enum type
    access_type_enum = postgresql.ENUM(name="access_type_enum")
    access_type_enum.drop(op.get_bind(), checkfirst=True)
