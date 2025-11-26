"""add_kb_settings_and_outbox_aggregate_type

Revision ID: 003
Revises: 002
Create Date: 2025-11-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add settings JSONB to knowledge_bases and aggregate_type to outbox."""
    # Add settings column to knowledge_bases
    op.add_column(
        "knowledge_bases",
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )

    # Add indexes on owner_id and status for knowledge_bases (per tech-spec)
    op.create_index("idx_kb_owner", "knowledge_bases", ["owner_id"])
    op.create_index("idx_kb_status", "knowledge_bases", ["status"])

    # Add aggregate_type column to outbox
    op.add_column(
        "outbox",
        sa.Column(
            "aggregate_type",
            sa.String(length=50),
            nullable=False,
            server_default="unknown",
        ),
    )

    # Remove the server_default after setting existing rows
    op.alter_column("outbox", "aggregate_type", server_default=None)


def downgrade() -> None:
    """Remove settings from knowledge_bases and aggregate_type from outbox."""
    op.drop_column("outbox", "aggregate_type")
    op.drop_index("idx_kb_status", table_name="knowledge_bases")
    op.drop_index("idx_kb_owner", table_name="knowledge_bases")
    op.drop_column("knowledge_bases", "settings")
