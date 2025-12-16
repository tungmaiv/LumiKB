"""add_groups_and_user_groups_tables

Revision ID: cecccdf66df7
Revises: 9c4424c51c68
Create Date: 2025-12-05 11:29:59.146596

Story 5.19: Group Management (AC-5.19.1)
- Creates groups table for organizing users
- Creates user_groups junction table for many-to-many relationship
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cecccdf66df7'
down_revision: Union[str, Sequence[str], None] = '9c4424c51c68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create groups and user_groups tables."""
    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_groups_is_active'), 'groups', ['is_active'], unique=False)
    op.create_index(op.f('ix_groups_name'), 'groups', ['name'], unique=True)

    # Create user_groups junction table
    op.create_table(
        'user_groups',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'group_id'),
    )
    op.create_index('idx_user_groups_group_id', 'user_groups', ['group_id'], unique=False)


def downgrade() -> None:
    """Drop groups and user_groups tables."""
    op.drop_index('idx_user_groups_group_id', table_name='user_groups')
    op.drop_table('user_groups')
    op.drop_index(op.f('ix_groups_name'), table_name='groups')
    op.drop_index(op.f('ix_groups_is_active'), table_name='groups')
    op.drop_table('groups')
