"""add onboarding fields to users

Revision ID: 7279836c14d9
Revises: e05dcbf6d840
Create Date: 2025-12-03 02:50:38.443590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7279836c14d9'
down_revision: Union[str, Sequence[str], None] = 'e05dcbf6d840'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add onboarding_completed field (default false for new users)
    op.add_column(
        'users',
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    # Add last_active field (nullable for future use)
    op.add_column(
        'users',
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True)
    )

    # Set existing users to onboarding_completed = true to avoid re-triggering
    op.execute('UPDATE users SET onboarding_completed = TRUE')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'last_active')
    op.drop_column('users', 'onboarding_completed')
