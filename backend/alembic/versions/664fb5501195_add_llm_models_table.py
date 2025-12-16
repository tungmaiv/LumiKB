"""add_llm_models_table

Revision ID: 664fb5501195
Revises: ca404d9346d2
Create Date: 2025-12-08 21:05:38.904170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '664fb5501195'
down_revision: Union[str, Sequence[str], None] = 'ca404d9346d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create llm_models table
    op.create_table(
        'llm_models',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('api_key_encrypted', sa.LargeBinary(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_llm_models_type'), 'llm_models', ['type'], unique=False)
    op.create_index(op.f('ix_llm_models_provider'), 'llm_models', ['provider'], unique=False)
    op.create_index(op.f('ix_llm_models_status'), 'llm_models', ['status'], unique=False)

    # Create partial unique index for is_default (only one default per type)
    op.execute(
        """
        CREATE UNIQUE INDEX idx_llm_models_default_unique
        ON llm_models (type)
        WHERE is_default = true
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop partial unique index
    op.execute("DROP INDEX IF EXISTS idx_llm_models_default_unique")

    # Drop regular indexes
    op.drop_index(op.f('ix_llm_models_status'), table_name='llm_models')
    op.drop_index(op.f('ix_llm_models_provider'), table_name='llm_models')
    op.drop_index(op.f('ix_llm_models_type'), table_name='llm_models')

    # Drop table
    op.drop_table('llm_models')
