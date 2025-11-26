"""Add document version tracking fields.

Revision ID: 005
Revises: 004
Create Date: 2025-11-24

Story: 2-12-document-re-upload-and-version-awareness
AC: 7 - Version awareness tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add version_number and version_history columns to documents table."""
    op.add_column(
        "documents",
        sa.Column(
            "version_number",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "version_history",
            JSONB(),
            server_default="[]",
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove version_number and version_history columns from documents table."""
    op.drop_column("documents", "version_history")
    op.drop_column("documents", "version_number")
