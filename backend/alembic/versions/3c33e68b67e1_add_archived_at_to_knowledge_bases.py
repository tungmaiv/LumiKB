"""add_archived_at_to_knowledge_bases

Revision ID: 3c33e68b67e1
Revises: 5ef2580afdf9
Create Date: 2025-12-10 16:04:14.202045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c33e68b67e1'
down_revision: Union[str, Sequence[str], None] = '5ef2580afdf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add archived_at column to knowledge_bases table for KB archive functionality.

    Story 7-24: KB Archive Backend
    - Adds archived_at timestamp column for tracking when a KB was archived
    - Creates partial index for efficient filtering of archived KBs
    """
    op.add_column(
        "knowledge_bases",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Index for efficient filtering of archived KBs
    op.create_index(
        "ix_knowledge_bases_archived_at",
        "knowledge_bases",
        ["archived_at"],
        postgresql_where=sa.text("archived_at IS NOT NULL"),
    )


def downgrade() -> None:
    """Remove archived_at column from knowledge_bases table."""
    op.drop_index("ix_knowledge_bases_archived_at", table_name="knowledge_bases")
    op.drop_column("knowledge_bases", "archived_at")
