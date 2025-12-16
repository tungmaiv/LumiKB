"""add_archived_at_to_documents

Revision ID: ca404d9346d2
Revises: 44d340d9f6fc
Create Date: 2025-12-07 11:52:41.157663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca404d9346d2'
down_revision: Union[str, Sequence[str], None] = '44d340d9f6fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add archived_at column to documents table for soft-archive functionality."""
    op.add_column(
        "documents",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Index for efficient filtering of archived documents
    op.create_index(
        "ix_documents_archived_at",
        "documents",
        ["archived_at"],
        postgresql_where=sa.text("archived_at IS NOT NULL"),
    )


def downgrade() -> None:
    """Remove archived_at column from documents table."""
    op.drop_index("ix_documents_archived_at", table_name="documents")
    op.drop_column("documents", "archived_at")
