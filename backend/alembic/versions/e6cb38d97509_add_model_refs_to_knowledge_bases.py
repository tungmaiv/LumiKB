"""add_model_refs_to_knowledge_bases

Revision ID: e6cb38d97509
Revises: 664fb5501195
Create Date: 2025-12-09 03:08:37.852321

Adds model references and RAG configuration to knowledge_bases table.
Story 7-10: KB Model Configuration
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6cb38d97509"
down_revision: Union[str, Sequence[str], None] = "664fb5501195"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add model references and RAG parameters to knowledge_bases."""
    # Add embedding model FK (nullable - existing KBs can have NULL)
    op.add_column(
        "knowledge_bases",
        sa.Column(
            "embedding_model_id",
            sa.UUID(),
            sa.ForeignKey("llm_models.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add generation model FK (nullable - existing KBs can have NULL)
    op.add_column(
        "knowledge_bases",
        sa.Column(
            "generation_model_id",
            sa.UUID(),
            sa.ForeignKey("llm_models.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add Qdrant collection metadata
    op.add_column(
        "knowledge_bases",
        sa.Column("qdrant_collection_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "knowledge_bases",
        sa.Column("qdrant_vector_size", sa.Integer(), nullable=True),
    )

    # Add KB-level RAG parameter overrides
    op.add_column(
        "knowledge_bases",
        sa.Column(
            "similarity_threshold", sa.Float(), server_default="0.7", nullable=True
        ),
    )
    op.add_column(
        "knowledge_bases",
        sa.Column("search_top_k", sa.Integer(), server_default="10", nullable=True),
    )
    op.add_column(
        "knowledge_bases",
        sa.Column("temperature", sa.Float(), nullable=True),
    )
    op.add_column(
        "knowledge_bases",
        sa.Column(
            "rerank_enabled", sa.Boolean(), server_default="false", nullable=True
        ),
    )

    # Create indexes for model FK lookups
    op.create_index(
        "ix_knowledge_bases_embedding_model_id",
        "knowledge_bases",
        ["embedding_model_id"],
    )
    op.create_index(
        "ix_knowledge_bases_generation_model_id",
        "knowledge_bases",
        ["generation_model_id"],
    )


def downgrade() -> None:
    """Remove model references and RAG parameters from knowledge_bases."""
    # Drop indexes
    op.drop_index("ix_knowledge_bases_generation_model_id", table_name="knowledge_bases")
    op.drop_index("ix_knowledge_bases_embedding_model_id", table_name="knowledge_bases")

    # Drop RAG parameter columns
    op.drop_column("knowledge_bases", "rerank_enabled")
    op.drop_column("knowledge_bases", "temperature")
    op.drop_column("knowledge_bases", "search_top_k")
    op.drop_column("knowledge_bases", "similarity_threshold")

    # Drop Qdrant metadata columns
    op.drop_column("knowledge_bases", "qdrant_vector_size")
    op.drop_column("knowledge_bases", "qdrant_collection_name")

    # Drop model FK columns
    op.drop_column("knowledge_bases", "generation_model_id")
    op.drop_column("knowledge_bases", "embedding_model_id")
