"""add_system_config_table

Revision ID: e05dcbf6d840
Revises: 46b7e5f40417
Create Date: 2025-12-02 23:49:14.887088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e05dcbf6d840'
down_revision: Union[str, Sequence[str], None] = '46b7e5f40417'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'system_config',
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )
    op.create_index('idx_system_config_key', 'system_config', ['key'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_system_config_key', 'system_config')
    op.drop_table('system_config')
