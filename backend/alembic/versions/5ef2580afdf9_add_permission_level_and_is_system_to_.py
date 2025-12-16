"""add_permission_level_and_is_system_to_groups

Story 7.11: Navigation Restructure with RBAC Default Groups
- Add permission_level column (1=User, 2=Operator, 3=Administrator)
- Add is_system column to protect system groups from deletion
- Seed three default system groups: Users, Operators, Administrators
- Assign existing superusers to Administrators group
- Assign existing non-superusers to Users group

Revision ID: 5ef2580afdf9
Revises: e6cb38d97509
Create Date: 2025-12-09 11:56:58.202308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ef2580afdf9'
down_revision: Union[str, Sequence[str], None] = 'e6cb38d97509'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# System group definitions
SYSTEM_GROUPS = [
    {"name": "Users", "description": "Default user group - basic access", "permission_level": 1},
    {"name": "Operators", "description": "Operators - can upload/delete documents and create KBs", "permission_level": 2},
    {"name": "Administrators", "description": "Administrators - full system access", "permission_level": 3},
]


def upgrade() -> None:
    """Add permission_level and is_system columns, seed default groups."""
    # 1. Add columns with defaults (nullable initially for permission_level)
    op.add_column(
        "groups",
        sa.Column(
            "permission_level",
            sa.Integer(),
            nullable=True,
            comment="Permission tier: 1=User, 2=Operator, 3=Administrator",
        ),
    )
    op.add_column(
        "groups",
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="System groups cannot be deleted",
        ),
    )

    # 2. Set default permission_level=1 for existing groups
    op.execute("UPDATE groups SET permission_level = 1 WHERE permission_level IS NULL")

    # 3. Make permission_level NOT NULL
    op.alter_column("groups", "permission_level", nullable=False, server_default=sa.text("1"))

    # 4. Create index on permission_level
    op.create_index("ix_groups_permission_level", "groups", ["permission_level"])

    # 5. Create system groups
    connection = op.get_bind()
    for group in SYSTEM_GROUPS:
        # Check if group already exists
        result = connection.execute(
            sa.text("SELECT id FROM groups WHERE name = :name"),
            {"name": group["name"]},
        )
        existing = result.fetchone()

        if existing:
            # Update existing group to be a system group
            connection.execute(
                sa.text(
                    "UPDATE groups SET permission_level = :level, is_system = true, is_active = true "
                    "WHERE name = :name"
                ),
                {"name": group["name"], "level": group["permission_level"]},
            )
        else:
            # Create new system group
            connection.execute(
                sa.text(
                    "INSERT INTO groups (name, description, permission_level, is_system, is_active) "
                    "VALUES (:name, :description, :level, true, true)"
                ),
                {
                    "name": group["name"],
                    "description": group["description"],
                    "level": group["permission_level"],
                },
            )

    # 6. Get system group IDs
    users_group = connection.execute(
        sa.text("SELECT id FROM groups WHERE name = 'Users'")
    ).fetchone()
    admins_group = connection.execute(
        sa.text("SELECT id FROM groups WHERE name = 'Administrators'")
    ).fetchone()

    if users_group and admins_group:
        # 7. Assign existing superusers to Administrators group (if not already members)
        connection.execute(
            sa.text(
                """
                INSERT INTO user_groups (user_id, group_id)
                SELECT u.id, :admin_group_id
                FROM users u
                WHERE u.is_superuser = true
                AND NOT EXISTS (
                    SELECT 1 FROM user_groups ug
                    WHERE ug.user_id = u.id AND ug.group_id = :admin_group_id
                )
                """
            ),
            {"admin_group_id": admins_group[0]},
        )

        # 8. Assign all existing users to Users group (if not already members)
        connection.execute(
            sa.text(
                """
                INSERT INTO user_groups (user_id, group_id)
                SELECT u.id, :users_group_id
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM user_groups ug
                    WHERE ug.user_id = u.id AND ug.group_id = :users_group_id
                )
                """
            ),
            {"users_group_id": users_group[0]},
        )


def downgrade() -> None:
    """Remove permission_level and is_system columns."""
    # Drop index
    op.drop_index("ix_groups_permission_level", table_name="groups")

    # Remove user_group memberships for system groups
    connection = op.get_bind()
    for group in SYSTEM_GROUPS:
        result = connection.execute(
            sa.text("SELECT id FROM groups WHERE name = :name AND is_system = true"),
            {"name": group["name"]},
        )
        group_row = result.fetchone()
        if group_row:
            connection.execute(
                sa.text("DELETE FROM user_groups WHERE group_id = :group_id"),
                {"group_id": group_row[0]},
            )
            connection.execute(
                sa.text("DELETE FROM groups WHERE id = :group_id"),
                {"group_id": group_row[0]},
            )

    # Drop columns
    op.drop_column("groups", "is_system")
    op.drop_column("groups", "permission_level")
