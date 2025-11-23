"""audit_schema_and_role

Revision ID: 002
Revises: 001
Create Date: 2025-11-23 04:09:34.418275

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit schema, table, indexes, and role with INSERT-only permissions."""
    # Create audit schema
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    # Create audit.events table
    op.create_table(
        "events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="audit",
    )

    # Create indexes for common query patterns
    op.create_index(
        "idx_audit_user",
        "events",
        ["user_id"],
        schema="audit",
    )
    op.create_index(
        "idx_audit_timestamp",
        "events",
        ["timestamp"],
        schema="audit",
    )
    op.create_index(
        "idx_audit_resource",
        "events",
        ["resource_type", "resource_id"],
        schema="audit",
    )

    # Create audit_writer role with INSERT-only permissions
    # Using IF NOT EXISTS for idempotency
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_writer') THEN
                CREATE ROLE audit_writer;
            END IF;
        END
        $$;
        """
    )

    # Grant usage on audit schema to audit_writer
    op.execute("GRANT USAGE ON SCHEMA audit TO audit_writer")

    # Grant INSERT-only permission on audit.events to audit_writer
    op.execute("GRANT INSERT ON audit.events TO audit_writer")


def downgrade() -> None:
    """Drop audit schema, table, and role."""
    # Revoke permissions from audit_writer
    op.execute("REVOKE ALL ON audit.events FROM audit_writer")
    op.execute("REVOKE USAGE ON SCHEMA audit FROM audit_writer")

    # Drop audit_writer role if it exists and has no members
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_writer') THEN
                DROP ROLE audit_writer;
            END IF;
        EXCEPTION
            WHEN dependent_objects_still_exist THEN
                RAISE NOTICE 'Role audit_writer has dependent objects, not dropped';
        END
        $$;
        """
    )

    # Drop indexes
    op.drop_index("idx_audit_resource", table_name="events", schema="audit")
    op.drop_index("idx_audit_timestamp", table_name="events", schema="audit")
    op.drop_index("idx_audit_user", table_name="events", schema="audit")

    # Drop audit.events table
    op.drop_table("events", schema="audit")

    # Drop audit schema
    op.execute("DROP SCHEMA IF EXISTS audit")
