"""add_tags_to_knowledge_bases

Revision ID: 24161041d664
Revises: f8a3d2e91b47
Create Date: 2025-12-06 02:42:24.990820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '24161041d664'
down_revision: Union[str, Sequence[str], None] = 'f8a3d2e91b47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tags column to knowledge_bases table."""
    op.add_column(
        'knowledge_bases',
        sa.Column(
            'tags',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='[]',
            nullable=False
        )
    )


def downgrade() -> None:
    """Remove tags column from knowledge_bases table."""
    op.drop_column('knowledge_bases', 'tags')
