"""initial_schema

Revision ID: 001
Revises:
Create Date: 2025-11-23 04:09:00.685290

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create enum types
    document_status = postgresql.ENUM(
        "PENDING",
        "PROCESSING",
        "READY",
        "FAILED",
        "ARCHIVED",
        name="document_status",
    )
    permission_level = postgresql.ENUM(
        "READ",
        "WRITE",
        "ADMIN",
        name="permission_level",
    )
    document_status.create(op.get_bind())
    permission_level.create(op.get_bind())

    # Create users table (FastAPI-Users compatible)
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # Create knowledge_bases table
    op.create_table(
        "knowledge_bases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create kb_permissions table
    op.create_table(
        "kb_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "permission_level",
            postgresql.ENUM(
                "READ", "WRITE", "ADMIN", name="permission_level", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["kb_id"],
            ["knowledge_bases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "kb_id", name="uq_kb_permissions_user_kb"),
    )

    # Create documents table
    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "PROCESSING",
                "READY",
                "FAILED",
                "ARCHIVED",
                name="document_status",
                create_type=False,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["kb_id"],
            ["knowledge_bases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create outbox table
    op.create_table(
        "outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index for finding unprocessed events
    op.create_index(
        "idx_outbox_unprocessed",
        "outbox",
        ["created_at"],
        postgresql_where=sa.text("processed_at IS NULL"),
    )


def downgrade() -> None:
    """Drop all tables and enum types."""
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index("idx_outbox_unprocessed", table_name="outbox")
    op.drop_table("outbox")
    op.drop_table("documents")
    op.drop_table("kb_permissions")
    op.drop_table("knowledge_bases")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Drop enum types
    postgresql.ENUM(name="document_status").drop(op.get_bind())
    postgresql.ENUM(name="permission_level").drop(op.get_bind())
