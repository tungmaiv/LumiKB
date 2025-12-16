"""Group service for business logic.

Story 5.19: Group Management (AC-5.19.1)
Story 7.11: Navigation Restructure with RBAC Default Groups
- AC-7.11.8: Block deletion of system groups
- AC-7.11.19: Last admin safety check
"""

from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.group import Group, UserGroup
from app.models.user import User
from app.schemas.group import GroupCreate, GroupUpdate
from app.services.audit_service import audit_service
from app.services.permission_service import PermissionService

logger = structlog.get_logger(__name__)


class GroupService:
    """Service for Group operations.

    Handles business logic including CRUD operations, membership management,
    and coordination with audit logging.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize GroupService with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def list_groups(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
    ) -> tuple[list[Group], int]:
        """List groups with pagination and optional search filter.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            search: Optional search term for group name.

        Returns:
            Tuple of (list of Groups, total count).
        """
        # Build base query for active groups
        query = select(Group).where(Group.is_active.is_(True))

        # Apply search filter if provided
        if search:
            query = query.where(Group.name.ilike(f"%{search}%"))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results with member count
        query = (
            query.options(selectinload(Group.user_groups))
            .order_by(Group.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        groups = list(result.scalars().all())

        return groups, total

    async def get_group(self, group_id: UUID) -> Group | None:
        """Get a group by ID with member details.

        Args:
            group_id: The group UUID.

        Returns:
            The Group with members loaded, or None if not found.
        """
        result = await self.session.execute(
            select(Group)
            .options(selectinload(Group.user_groups).selectinload(UserGroup.user))
            .where(Group.id == group_id, Group.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def create_group(
        self,
        data: GroupCreate,
        admin: User,
    ) -> Group:
        """Create a new group.

        Args:
            data: Group creation data.
            admin: The admin user creating the group.

        Returns:
            The newly created Group.

        Raises:
            ValueError: If group name already exists.
        """
        # Check for duplicate name
        existing = await self.session.execute(
            select(Group).where(Group.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Group name already exists")

        # Create the group
        group = Group(
            name=data.name,
            description=data.description,
        )
        self.session.add(group)
        await self.session.flush()

        # Audit log
        await audit_service.log_event(
            action="group.created",
            resource_type="group",
            user_id=admin.id,
            resource_id=group.id,
            details={"name": group.name},
        )

        logger.info(
            "group_created",
            group_id=str(group.id),
            name=group.name,
            created_by=str(admin.id),
        )

        return group

    async def update_group(
        self,
        group_id: UUID,
        data: GroupUpdate,
        admin: User,
    ) -> Group | None:
        """Update a group.

        Args:
            group_id: The group UUID.
            data: Update data.
            admin: The admin user performing the update.

        Returns:
            The updated Group, or None if not found.

        Raises:
            ValueError: If new name conflicts with existing group.
        """
        # Get the group
        result = await self.session.execute(
            select(Group).where(Group.id == group_id, Group.is_active.is_(True))
        )
        group = result.scalar_one_or_none()

        if not group:
            return None

        # Track changes for audit
        changes: dict[str, dict[str, str | bool | None]] = {}

        # Check for duplicate name if name is being changed
        if data.name is not None and data.name != group.name:
            existing = await self.session.execute(
                select(Group).where(Group.name == data.name, Group.id != group_id)
            )
            if existing.scalar_one_or_none():
                raise ValueError("Group name already exists")
            changes["name"] = {"old": group.name, "new": data.name}
            group.name = data.name

        if data.description is not None and data.description != group.description:
            changes["description"] = {"old": group.description, "new": data.description}
            group.description = data.description

        if data.is_active is not None and data.is_active != group.is_active:
            changes["is_active"] = {"old": group.is_active, "new": data.is_active}
            group.is_active = data.is_active

        if changes:
            await self.session.flush()
            await self.session.refresh(group)

            # Audit log
            await audit_service.log_event(
                action="group.updated",
                resource_type="group",
                user_id=admin.id,
                resource_id=group_id,
                details={"changes": changes},
            )

            logger.info(
                "group_updated",
                group_id=str(group_id),
                changes=list(changes.keys()),
                updated_by=str(admin.id),
            )

        return group

    async def delete_group(
        self,
        group_id: UUID,
        admin: User,
    ) -> bool:
        """Soft delete a group by setting is_active to False.

        AC-7.11.8: System groups cannot be deleted.

        Args:
            group_id: The group UUID.
            admin: The admin user performing the deletion.

        Returns:
            True if deleted successfully, False if not found.

        Raises:
            ValueError: If attempting to delete a system group.
        """
        # Get the group
        result = await self.session.execute(
            select(Group).where(Group.id == group_id, Group.is_active.is_(True))
        )
        group = result.scalar_one_or_none()

        if not group:
            return False

        # AC-7.11.8: Block deletion of system groups
        if group.is_system:
            raise ValueError("Cannot delete system groups")

        # Soft delete
        group.is_active = False
        await self.session.flush()

        # Audit log
        await audit_service.log_event(
            action="group.deleted",
            resource_type="group",
            user_id=admin.id,
            resource_id=group_id,
            details={"name": group.name},
        )

        logger.info(
            "group_deleted",
            group_id=str(group_id),
            name=group.name,
            deleted_by=str(admin.id),
        )

        return True

    async def add_members(
        self,
        group_id: UUID,
        user_ids: list[UUID],
        admin: User,
    ) -> int:
        """Add members to a group.

        Args:
            group_id: The group UUID.
            user_ids: List of user IDs to add.
            admin: The admin user performing the action.

        Returns:
            Number of members successfully added.

        Raises:
            ValueError: If group not found.
        """
        # Verify group exists and is active
        group_result = await self.session.execute(
            select(Group).where(Group.id == group_id, Group.is_active.is_(True))
        )
        group = group_result.scalar_one_or_none()
        if not group:
            raise ValueError("Group not found")

        # Get existing memberships for this group
        existing_result = await self.session.execute(
            select(UserGroup.user_id).where(UserGroup.group_id == group_id)
        )
        existing_user_ids = set(existing_result.scalars().all())

        # Filter out users that are already members
        new_user_ids = [uid for uid in user_ids if uid not in existing_user_ids]

        if not new_user_ids:
            return 0

        # Verify users exist
        users_result = await self.session.execute(
            select(User.id).where(User.id.in_(new_user_ids))
        )
        valid_user_ids = set(users_result.scalars().all())

        # Create new memberships
        added_count = 0
        for user_id in new_user_ids:
            if user_id in valid_user_ids:
                user_group = UserGroup(
                    user_id=user_id,
                    group_id=group_id,
                )
                self.session.add(user_group)
                added_count += 1

                # Audit log per member
                await audit_service.log_event(
                    action="group.member_added",
                    resource_type="group",
                    user_id=admin.id,
                    resource_id=group_id,
                    details={"added_user_id": str(user_id)},
                )

        await self.session.flush()

        logger.info(
            "group_members_added",
            group_id=str(group_id),
            added_count=added_count,
            added_by=str(admin.id),
        )

        return added_count

    async def remove_member(
        self,
        group_id: UUID,
        user_id: UUID,
        admin: User,
    ) -> bool:
        """Remove a member from a group.

        AC-7.11.19: Prevents removing the last administrator.

        Args:
            group_id: The group UUID.
            user_id: The user ID to remove.
            admin: The admin user performing the action.

        Returns:
            True if removed successfully, False if membership not found.

        Raises:
            ValueError: If group not found or if attempting to remove last admin.
        """
        # Verify group exists and is active
        group_result = await self.session.execute(
            select(Group).where(Group.id == group_id, Group.is_active.is_(True))
        )
        if not group_result.scalar_one_or_none():
            raise ValueError("Group not found")

        # AC-7.11.19: Check last admin safety
        permission_service = PermissionService(self.session)
        can_remove, error_msg = await permission_service.can_remove_from_administrators(
            user_id, group_id
        )
        if not can_remove:
            raise ValueError(error_msg or "Cannot remove user from this group")

        # Find the membership
        result = await self.session.execute(
            select(UserGroup).where(
                UserGroup.group_id == group_id,
                UserGroup.user_id == user_id,
            )
        )
        membership = result.scalar_one_or_none()

        if not membership:
            return False

        # Delete the membership
        await self.session.delete(membership)
        await self.session.flush()

        # Audit log
        await audit_service.log_event(
            action="group.member_removed",
            resource_type="group",
            user_id=admin.id,
            resource_id=group_id,
            details={"removed_user_id": str(user_id)},
        )

        logger.info(
            "group_member_removed",
            group_id=str(group_id),
            removed_user_id=str(user_id),
            removed_by=str(admin.id),
        )

        return True
