"""add_document_upload_fields

Revision ID: 004
Revises: 003
Create Date: 2025-11-24

Adds new fields to documents table for upload functionality:
- original_filename, mime_type, file_size_bytes, checksum
- processing_started_at, processing_completed_at
- retry_count, uploaded_by, deleted_at
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add document upload fields."""
    # Add new columns to documents table
    op.add_column(
        "documents",
        sa.Column("original_filename", sa.String(255), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("mime_type", sa.String(100), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("checksum", sa.String(64), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add foreign key for uploaded_by
    op.create_foreign_key(
        "fk_documents_uploaded_by",
        "documents",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill existing rows with defaults (required for NOT NULL columns)
    # Using name as original_filename, text/plain as mime_type, 0 as file_size, empty checksum
    op.execute(
        """
        UPDATE documents
        SET original_filename = name,
            mime_type = 'application/octet-stream',
            file_size_bytes = 0,
            checksum = ''
        WHERE original_filename IS NULL
        """
    )

    # Now make the columns NOT NULL
    op.alter_column("documents", "original_filename", nullable=False)
    op.alter_column("documents", "mime_type", nullable=False)
    op.alter_column("documents", "file_size_bytes", nullable=False)
    op.alter_column("documents", "checksum", nullable=False)

    # Add index for soft deletes
    op.create_index(
        "idx_documents_deleted_at",
        "documents",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Add index for kb_id + status (common query pattern)
    op.create_index(
        "idx_documents_kb_status",
        "documents",
        ["kb_id", "status"],
    )


def downgrade() -> None:
    """Remove document upload fields."""
    # Drop indexes
    op.drop_index("idx_documents_kb_status", table_name="documents")
    op.drop_index("idx_documents_deleted_at", table_name="documents")

    # Drop foreign key
    op.drop_constraint("fk_documents_uploaded_by", "documents", type_="foreignkey")

    # Drop columns
    op.drop_column("documents", "deleted_at")
    op.drop_column("documents", "uploaded_by")
    op.drop_column("documents", "retry_count")
    op.drop_column("documents", "processing_completed_at")
    op.drop_column("documents", "processing_started_at")
    op.drop_column("documents", "checksum")
    op.drop_column("documents", "file_size_bytes")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "original_filename")
