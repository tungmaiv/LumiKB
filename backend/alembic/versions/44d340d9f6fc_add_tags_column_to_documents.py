"""add_tags_column_to_documents

Revision ID: 44d340d9f6fc
Revises: 38f8bc466800
Create Date: 2025-12-06 17:00:10.034654

Story 5-22: Add tags column to documents for document categorization.
Tags are stored as JSONB array for efficient filtering and searching.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "44d340d9f6fc"
down_revision: Union[str, Sequence[str], None] = "38f8bc466800"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tags column to documents table."""
    op.add_column(
        "documents",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    # Add GIN index for efficient tag filtering
    op.create_index(
        "idx_documents_tags",
        "documents",
        ["tags"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Remove tags column from documents table."""
    op.drop_index("idx_documents_tags", table_name="documents", postgresql_using="gin")
    op.drop_column("documents", "tags")
