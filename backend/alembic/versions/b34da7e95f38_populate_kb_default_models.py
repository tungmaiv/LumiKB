"""populate_kb_default_models

Revision ID: b34da7e95f38
Revises: 31eea0de45a7
Create Date: 2025-12-17 18:19:56.731951

Populates null embedding_model_id and generation_model_id fields in
knowledge_bases table with the system default models.

This ensures all KBs always have explicit model references rather than
relying on runtime default resolution.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'b34da7e95f38'
down_revision: Union[str, Sequence[str], None] = '31eea0de45a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Populate null model IDs with system defaults."""
    conn = op.get_bind()

    # Get default embedding model
    default_embedding = conn.execute(
        text("""
            SELECT id FROM llm_models
            WHERE type = 'embedding'
            AND is_default = true
            AND status = 'active'
            LIMIT 1
        """)
    ).scalar()

    # Get default generation model
    default_generation = conn.execute(
        text("""
            SELECT id FROM llm_models
            WHERE type = 'generation'
            AND is_default = true
            AND status = 'active'
            LIMIT 1
        """)
    ).scalar()

    # Update KBs with null embedding_model_id
    if default_embedding:
        result = conn.execute(
            text("""
                UPDATE knowledge_bases
                SET embedding_model_id = :model_id
                WHERE embedding_model_id IS NULL
            """),
            {"model_id": default_embedding}
        )
        print(f"Updated {result.rowcount} KBs with default embedding model")

    # Update KBs with null generation_model_id
    if default_generation:
        result = conn.execute(
            text("""
                UPDATE knowledge_bases
                SET generation_model_id = :model_id
                WHERE generation_model_id IS NULL
            """),
            {"model_id": default_generation}
        )
        print(f"Updated {result.rowcount} KBs with default generation model")


def downgrade() -> None:
    """Downgrade - no action needed.

    We don't revert to null as that would cause data loss.
    The forward migration is safe and additive.
    """
    pass
