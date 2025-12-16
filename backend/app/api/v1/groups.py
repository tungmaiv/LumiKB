"""Group Management API routes.

Story 5.19: Group Management (AC-5.19.1, AC-5.19.4, AC-5.19.6)

Provides admin-only endpoints for group management:
- GET /api/v1/admin/groups - List groups with pagination and search
- POST /api/v1/admin/groups - Create a new group
- GET /api/v1/admin/groups/{group_id} - Get group details with members
- PATCH /api/v1/admin/groups/{group_id} - Update group
- DELETE /api/v1/admin/groups/{group_id} - Soft delete group
- POST /api/v1/admin/groups/{group_id}/members - Add members to group
- DELETE /api/v1/admin/groups/{group_id}/members/{user_id} - Remove member
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_administrator
from app.core.database import get_async_session
from app.models.user import User
from app.schemas.group import (
    GroupCreate,
    GroupMemberAdd,
    GroupMemberAddResponse,
    GroupMemberRead,
    GroupRead,
    GroupUpdate,
    GroupWithMembers,
    PaginatedGroupResponse,
)
from app.services.group_service import GroupService

router = APIRouter(prefix="/admin/groups", tags=["admin-groups"])


@router.get(
    "",
    response_model=PaginatedGroupResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def list_groups(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    ),
    search: str | None = Query(
        default=None, max_length=255, description="Search by group name"
    ),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedGroupResponse:
    """List all groups with pagination and optional search.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        page: Page number (1-indexed, default 1).
        page_size: Items per page (default 20, max 100).
        search: Optional search term for group name.
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        PaginatedGroupResponse: Paginated list of groups with member counts.
    """
    service = GroupService(session)
    skip = (page - 1) * page_size
    groups, total = await service.list_groups(skip=skip, limit=page_size, search=search)

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return PaginatedGroupResponse(
        items=[
            GroupRead(
                id=g.id,
                name=g.name,
                description=g.description,
                is_active=g.is_active,
                permission_level=g.permission_level,
                is_system=g.is_system,
                member_count=g.member_count,
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
            for g in groups
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=GroupRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        409: {"description": "Group name already exists"},
    },
)
async def create_group(
    data: GroupCreate,
    admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> GroupRead:
    """Create a new group.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        data: Group creation data (name, description).
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        GroupRead: The created group.

    Raises:
        HTTPException: 409 if group name already exists.
    """
    service = GroupService(session)

    try:
        group = await service.create_group(data, admin)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    return GroupRead(
        id=group.id,
        name=group.name,
        description=group.description,
        is_active=group.is_active,
        permission_level=group.permission_level,
        is_system=group.is_system,
        member_count=0,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.get(
    "/{group_id}",
    response_model=GroupWithMembers,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        404: {"description": "Group not found"},
    },
)
async def get_group(
    group_id: UUID,
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> GroupWithMembers:
    """Get group details including member list.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        group_id: The group UUID.
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        GroupWithMembers: Group details with member list.

    Raises:
        HTTPException: 404 if group not found.
    """
    service = GroupService(session)
    group = await service.get_group(group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return GroupWithMembers(
        id=group.id,
        name=group.name,
        description=group.description,
        is_active=group.is_active,
        permission_level=group.permission_level,
        is_system=group.is_system,
        member_count=group.member_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=[
            GroupMemberRead(
                id=ug.user.id,
                email=ug.user.email,
                is_active=ug.user.is_active,
                joined_at=ug.created_at,
            )
            for ug in group.user_groups
        ],
    )


@router.patch(
    "/{group_id}",
    response_model=GroupRead,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        404: {"description": "Group not found"},
        409: {"description": "Group name already exists"},
    },
)
async def update_group(
    group_id: UUID,
    data: GroupUpdate,
    admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> GroupRead:
    """Update a group.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        group_id: The group UUID.
        data: Update data (name, description, is_active).
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        GroupRead: The updated group.

    Raises:
        HTTPException: 404 if group not found, 409 if name conflicts.
    """
    service = GroupService(session)

    try:
        group = await service.update_group(group_id, data, admin)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )
        await session.commit()
        await session.refresh(group)
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    return GroupRead(
        id=group.id,
        name=group.name,
        description=group.description,
        is_active=group.is_active,
        permission_level=group.permission_level,
        is_system=group.is_system,
        member_count=group.member_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        404: {"description": "Group not found"},
    },
)
async def delete_group(
    group_id: UUID,
    admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Soft delete a group by setting is_active to False.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        group_id: The group UUID.
        admin: Current authenticated superuser.
        session: Database session.

    Raises:
        HTTPException: 404 if group not found.
    """
    service = GroupService(session)
    deleted = await service.delete_group(group_id, admin)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    await session.commit()


@router.post(
    "/{group_id}/members",
    response_model=GroupMemberAddResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        404: {"description": "Group not found"},
    },
)
async def add_group_members(
    group_id: UUID,
    data: GroupMemberAdd,
    admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> GroupMemberAddResponse:
    """Add members to a group.

    Users that are already members will be skipped.
    Invalid user IDs will be silently ignored.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        group_id: The group UUID.
        data: List of user IDs to add.
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        GroupMemberAddResponse: Number of members successfully added.

    Raises:
        HTTPException: 404 if group not found.
    """
    service = GroupService(session)

    try:
        added_count = await service.add_members(group_id, data.user_ids, admin)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return GroupMemberAddResponse(added_count=added_count)


@router.delete(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        404: {"description": "Group or membership not found"},
    },
)
async def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Remove a member from a group.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        group_id: The group UUID.
        user_id: The user UUID to remove.
        admin: Current authenticated superuser.
        session: Database session.

    Raises:
        HTTPException: 404 if group or membership not found.
    """
    service = GroupService(session)

    try:
        removed = await service.remove_member(group_id, user_id, admin)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this group",
            )
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
