"""Group test data factories for parallel-safe, schema-resilient test data.

Story 5.19: Group Management

Usage:
    from tests.factories import create_group, create_group_data

    # Create group model instance
    group = create_group(name="Engineering")

    # Create group API payload
    group_data = create_group_data()

    # Create group with members
    group = create_group_with_members(member_count=5)
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.models.group import Group


# Counter for unique group names
_group_counter = 0


def _get_unique_group_name() -> str:
    """Generate unique group name for parallel test safety."""
    global _group_counter
    _group_counter += 1
    return f"TestGroup_{_group_counter}_{uuid.uuid4().hex[:8]}"


def create_group_data(
    name: str | None = None,
    description: str | None = None,
) -> dict:
    """Create group API payload for POST /api/v1/admin/groups.

    Args:
        name: Group name (defaults to unique name).
        description: Group description (optional).

    Returns:
        dict: API payload for group creation.
    """
    return {
        "name": name or _get_unique_group_name(),
        "description": description,
    }


def create_group_update_data(
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict:
    """Create group update API payload for PATCH /api/v1/admin/groups/{id}.

    Only includes fields that are not None.

    Args:
        name: New group name (optional).
        description: New description (optional).
        is_active: New active status (optional).

    Returns:
        dict: API payload for group update.
    """
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if is_active is not None:
        data["is_active"] = is_active
    return data


def create_member_add_data(user_ids: list[str | UUID]) -> dict:
    """Create member add API payload for POST /api/v1/admin/groups/{id}/members.

    Args:
        user_ids: List of user IDs to add to group.

    Returns:
        dict: API payload for adding members.
    """
    return {"user_ids": [str(uid) for uid in user_ids]}


def create_group(
    name: str | None = None,
    description: str | None = None,
    is_active: bool = True,
    group_id: UUID | None = None,
) -> "Group":
    """Create a Group model instance (not persisted).

    Args:
        name: Group name (defaults to unique name).
        description: Group description (optional).
        is_active: Whether group is active (default True).
        group_id: Specific UUID for the group (optional).

    Returns:
        Group: Group model instance.
    """
    from app.models.group import Group

    return Group(
        id=group_id or uuid.uuid4(),
        name=name or _get_unique_group_name(),
        description=description,
        is_active=is_active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def create_group_response(
    group_id: UUID | str | None = None,
    name: str | None = None,
    description: str | None = None,
    is_active: bool = True,
    member_count: int = 0,
) -> dict:
    """Create expected group response shape for API assertions.

    Args:
        group_id: Group UUID (defaults to random).
        name: Group name (defaults to unique name).
        description: Group description (optional).
        is_active: Whether group is active (default True).
        member_count: Number of members (default 0).

    Returns:
        dict: Expected API response structure.
    """
    return {
        "id": str(group_id) if group_id else str(uuid.uuid4()),
        "name": name or _get_unique_group_name(),
        "description": description,
        "is_active": is_active,
        "member_count": member_count,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }


def create_paginated_groups_response(
    groups: list[dict] | None = None,
    total: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Create expected paginated groups response.

    Args:
        groups: List of group response dicts (optional).
        total: Total count (defaults to len(groups)).
        page: Current page number (default 1).
        page_size: Page size (default 20).

    Returns:
        dict: Expected paginated API response.
    """
    items = groups or []
    total_count = total if total is not None else len(items)
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_group_with_members_response(
    group_id: UUID | str | None = None,
    name: str | None = None,
    description: str | None = None,
    is_active: bool = True,
    members: list[dict] | None = None,
) -> dict:
    """Create expected group with members response.

    Args:
        group_id: Group UUID (defaults to random).
        name: Group name (defaults to unique name).
        description: Group description (optional).
        is_active: Whether group is active (default True).
        members: List of member dicts (optional).

    Returns:
        dict: Expected API response with members.
    """
    member_list = members or []
    return {
        "id": str(group_id) if group_id else str(uuid.uuid4()),
        "name": name or _get_unique_group_name(),
        "description": description,
        "is_active": is_active,
        "member_count": len(member_list),
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "members": member_list,
    }


def create_group_member_response(
    user_id: UUID | str | None = None,
    email: str | None = None,
    is_active: bool = True,
) -> dict:
    """Create expected group member response shape.

    Args:
        user_id: User UUID (defaults to random).
        email: User email (defaults to unique email).
        is_active: Whether user is active (default True).

    Returns:
        dict: Expected member response structure.
    """
    global _group_counter
    _group_counter += 1
    return {
        "id": str(user_id) if user_id else str(uuid.uuid4()),
        "email": email or f"member_{_group_counter}_{uuid.uuid4().hex[:8]}@example.com",
        "is_active": is_active,
        "joined_at": datetime.now(UTC).isoformat(),
    }
