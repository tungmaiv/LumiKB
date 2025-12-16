"""add_kb_group_permissions_table

Revision ID: f8a3d2e91b47
Revises: cecccdf66df7
Create Date: 2025-12-05 15:00:00.000000

Story 5.20: Role & KB Permission Management UI (AC-5.20.5)
- Creates kb_group_permissions table for group-level KB permissions
- Reuses existing permission_level ENUM (READ, WRITE, ADMIN)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a3d2e91b47'
down_revision: Union[str, Sequence[str], None] = 'cecccdf66df7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create kb_group_permissions table."""
    # Create kb_group_permissions table
    # Reuse existing permission_level ENUM from kb_permissions table
    permission_level = sa.Enum('READ', 'WRITE', 'ADMIN', name='permission_level', create_type=False)

    op.create_table(
        'kb_group_permissions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('kb_id', sa.UUID(), nullable=False),
        sa.Column('permission_level', permission_level, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['kb_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'kb_id', name='uq_kb_group_permissions_group_kb'),
    )
    op.create_index('idx_kb_group_permissions_kb_id', 'kb_group_permissions', ['kb_id'], unique=False)
    op.create_index('idx_kb_group_permissions_group_id', 'kb_group_permissions', ['group_id'], unique=False)


def downgrade() -> None:
    """Drop kb_group_permissions table."""
    op.drop_index('idx_kb_group_permissions_group_id', table_name='kb_group_permissions')
    op.drop_index('idx_kb_group_permissions_kb_id', table_name='kb_group_permissions')
    op.drop_table('kb_group_permissions')
