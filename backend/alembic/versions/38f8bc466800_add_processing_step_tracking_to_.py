"""add_processing_step_tracking_to_documents

Revision ID: 38f8bc466800
Revises: 24161041d664
Create Date: 2025-12-06 11:20:25.043026

Story 5-23: Document Processing Progress Screen
Adds step-level tracking columns to the documents table for detailed
pipeline progress monitoring.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '38f8bc466800'
down_revision: Union[str, Sequence[str], None] = '24161041d664'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add processing step tracking columns to documents table.

    New columns:
    - processing_steps: JSONB tracking status of each pipeline step
    - current_step: VARCHAR(20) for current processing step
    - step_errors: JSONB for step-specific error messages

    Indexes:
    - idx_documents_current_step: For filtering by step
    - idx_documents_status_step: For combined status+step filtering
    """
    # Add processing_steps JSONB column
    op.add_column(
        'documents',
        sa.Column(
            'processing_steps',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='{}',
            nullable=False
        )
    )

    # Add current_step VARCHAR column
    op.add_column(
        'documents',
        sa.Column(
            'current_step',
            sa.String(20),
            server_default='upload',
            nullable=False
        )
    )

    # Add step_errors JSONB column
    op.add_column(
        'documents',
        sa.Column(
            'step_errors',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='{}',
            nullable=False
        )
    )

    # Add indexes for efficient filtering
    op.create_index(
        'idx_documents_current_step',
        'documents',
        ['current_step']
    )

    op.create_index(
        'idx_documents_status_step',
        'documents',
        ['status', 'current_step']
    )


def downgrade() -> None:
    """Remove processing step tracking columns from documents table."""
    # Drop indexes first
    op.drop_index('idx_documents_status_step', table_name='documents')
    op.drop_index('idx_documents_current_step', table_name='documents')

    # Drop columns
    op.drop_column('documents', 'step_errors')
    op.drop_column('documents', 'current_step')
    op.drop_column('documents', 'processing_steps')
