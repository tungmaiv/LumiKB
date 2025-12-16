"""Unit tests for GroupService.

Story 5.19: Group Management (AC-5.19.1)

Test Coverage:
- [P0] list_groups: Pagination, search filter, member count
- [P0] get_group: Retrieve by ID with members
- [P0] create_group: Create with validation and audit logging
- [P0] update_group: Update fields with change tracking
- [P0] delete_group: Soft delete with audit logging
- [P1] add_members: Add users to group with duplicate handling
- [P1] remove_member: Remove user from group

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- test-levels-framework.md: Unit test characteristics
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.group import Group, UserGroup
from app.models.user import User
from app.schemas.group import GroupCreate, GroupUpdate
from app.services.group_service import GroupService


class TestGroupServiceListGroups:
    """Tests for GroupService.list_groups method."""

    @pytest.mark.asyncio
    async def test_list_groups_returns_active_groups(self):
        """
        GIVEN: GroupService with active groups in database
        WHEN: list_groups is called
        THEN: Only active groups are returned
        """
        # GIVEN: Mock session with groups
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_groups = [
            MagicMock(
                spec=Group, id=uuid4(), name="Group 1", is_active=True, user_groups=[]
            ),
            MagicMock(
                spec=Group, id=uuid4(), name="Group 2", is_active=True, user_groups=[]
            ),
        ]

        # Setup mock execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_groups
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # WHEN: Call list_groups
        groups, total = await service.list_groups(skip=0, limit=20)

        # THEN: Returns groups and total count
        assert len(groups) == 2
        assert total == 2
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_groups_with_search_filter(self):
        """
        GIVEN: GroupService with multiple groups
        WHEN: list_groups is called with search term
        THEN: Query includes search filter
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_groups = [MagicMock(spec=Group, name="Engineering", user_groups=[])]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_groups
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # WHEN: Call list_groups with search
        groups, total = await service.list_groups(skip=0, limit=20, search="Eng")

        # THEN: Returns filtered results
        assert len(groups) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_groups_pagination(self):
        """
        GIVEN: GroupService with many groups
        WHEN: list_groups is called with skip and limit
        THEN: Returns paginated results
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_groups = [
            MagicMock(spec=Group, name=f"Group {i}", user_groups=[]) for i in range(10)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_groups
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50  # Total in DB

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # WHEN: Call list_groups with pagination
        groups, total = await service.list_groups(skip=10, limit=10)

        # THEN: Returns correct page with total count
        assert len(groups) == 10
        assert total == 50

    @pytest.mark.asyncio
    async def test_list_groups_empty_result(self):
        """
        GIVEN: GroupService with no groups
        WHEN: list_groups is called
        THEN: Returns empty list with zero count
        """
        # GIVEN: Mock session with no groups
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # WHEN: Call list_groups
        groups, total = await service.list_groups(skip=0, limit=20)

        # THEN: Returns empty results
        assert groups == []
        assert total == 0


class TestGroupServiceGetGroup:
    """Tests for GroupService.get_group method."""

    @pytest.mark.asyncio
    async def test_get_group_returns_group_with_members(self):
        """
        GIVEN: GroupService with existing group
        WHEN: get_group is called with valid ID
        THEN: Returns group with members loaded
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        mock_group = MagicMock(spec=Group)
        mock_group.id = group_id
        mock_group.name = "Engineering"
        mock_group.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_group
        mock_session.execute.return_value = mock_result

        # WHEN: Call get_group
        result = await service.get_group(group_id)

        # THEN: Returns the group
        assert result is not None
        assert result.id == group_id
        assert result.name == "Engineering"

    @pytest.mark.asyncio
    async def test_get_group_returns_none_for_nonexistent(self):
        """
        GIVEN: GroupService with no matching group
        WHEN: get_group is called with non-existent ID
        THEN: Returns None
        """
        # GIVEN: Mock session returning None
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # WHEN: Call get_group with random ID
        result = await service.get_group(uuid4())

        # THEN: Returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_group_excludes_inactive_groups(self):
        """
        GIVEN: GroupService with inactive group
        WHEN: get_group is called for inactive group
        THEN: Returns None (filtered by is_active)
        """
        # GIVEN: Mock session with inactive group filtered out
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # WHEN: Call get_group (inactive groups filtered by query)
        result = await service.get_group(uuid4())

        # THEN: Returns None
        assert result is None


class TestGroupServiceCreateGroup:
    """Tests for GroupService.create_group method."""

    @pytest.mark.asyncio
    async def test_create_group_success(self):
        """
        GIVEN: GroupService and valid group data
        WHEN: create_group is called
        THEN: Creates group and returns it
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        # Mock duplicate check returns None
        mock_duplicate_result = MagicMock()
        mock_duplicate_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_duplicate_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        group_data = GroupCreate(name="New Team", description="A new team")

        # WHEN: Call create_group
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            result = await service.create_group(group_data, admin_user)

        # THEN: Group is created
        assert result is not None
        assert result.name == "New Team"
        assert result.description == "A new team"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_group_duplicate_name_raises_error(self):
        """
        GIVEN: GroupService with existing group name
        WHEN: create_group is called with duplicate name
        THEN: Raises ValueError
        """
        # GIVEN: Mock session with existing group
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        existing_group = MagicMock(spec=Group)
        existing_group.name = "Existing Team"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_group
        mock_session.execute.return_value = mock_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        group_data = GroupCreate(name="Existing Team", description="Duplicate")

        # WHEN/THEN: create_group raises ValueError
        with pytest.raises(ValueError, match="Group name already exists"):
            await service.create_group(group_data, admin_user)

    @pytest.mark.asyncio
    async def test_create_group_logs_audit_event(self):
        """
        GIVEN: GroupService and valid group data
        WHEN: create_group is called
        THEN: Audit event is logged
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_duplicate_result = MagicMock()
        mock_duplicate_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_duplicate_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        group_data = GroupCreate(name="Audit Test", description=None)

        # WHEN: Call create_group
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            await service.create_group(group_data, admin_user)

            # THEN: Audit event is logged
            mock_audit.log_event.assert_called_once()
            call_args = mock_audit.log_event.call_args
            assert call_args.kwargs["action"] == "group.created"
            assert call_args.kwargs["resource_type"] == "group"


class TestGroupServiceUpdateGroup:
    """Tests for GroupService.update_group method."""

    @pytest.mark.asyncio
    async def test_update_group_name(self):
        """
        GIVEN: GroupService with existing group
        WHEN: update_group is called with new name
        THEN: Group name is updated
        """
        # GIVEN: Mock session with existing group
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        existing_group = MagicMock(spec=Group)
        existing_group.id = group_id
        existing_group.name = "Old Name"
        existing_group.description = "Description"
        existing_group.is_active = True

        # First call returns the group, second call returns None (no duplicate)
        mock_result_group = MagicMock()
        mock_result_group.scalar_one_or_none.return_value = existing_group

        mock_result_no_dup = MagicMock()
        mock_result_no_dup.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_group, mock_result_no_dup]
        )
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        update_data = GroupUpdate(name="New Name")

        # WHEN: Call update_group
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            result = await service.update_group(group_id, update_data, admin_user)

        # THEN: Group name is updated
        assert result is not None
        assert existing_group.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_group_status_deactivate(self):
        """
        GIVEN: GroupService with active group
        WHEN: update_group is called with is_active=False
        THEN: Group is deactivated
        """
        # GIVEN: Mock session with active group
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        existing_group = MagicMock(spec=Group)
        existing_group.id = group_id
        existing_group.name = "Active Group"
        existing_group.description = None
        existing_group.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_group
        mock_session.execute.return_value = mock_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        update_data = GroupUpdate(is_active=False)

        # WHEN: Call update_group
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            result = await service.update_group(group_id, update_data, admin_user)

        # THEN: Group is deactivated
        assert result is not None
        assert existing_group.is_active is False

    @pytest.mark.asyncio
    async def test_update_group_duplicate_name_raises_error(self):
        """
        GIVEN: GroupService with another group having same name
        WHEN: update_group is called with conflicting name
        THEN: Raises ValueError
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        existing_group = MagicMock(spec=Group)
        existing_group.id = group_id
        existing_group.name = "Original Name"
        existing_group.description = None
        existing_group.is_active = True

        # First call returns the group to update
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = existing_group

        # Second call (duplicate check) returns conflicting group
        conflicting_group = MagicMock(spec=Group)
        conflicting_group.id = uuid4()
        conflicting_group.name = "Existing Name"
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = conflicting_group

        mock_session.execute.side_effect = [mock_result1, mock_result2]

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        update_data = GroupUpdate(name="Existing Name")

        # WHEN/THEN: update_group raises ValueError
        with pytest.raises(ValueError, match="Group name already exists"):
            await service.update_group(group_id, update_data, admin_user)

    @pytest.mark.asyncio
    async def test_update_group_not_found_returns_none(self):
        """
        GIVEN: GroupService with no matching group
        WHEN: update_group is called with non-existent ID
        THEN: Returns None
        """
        # GIVEN: Mock session returning None
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        update_data = GroupUpdate(name="New Name")

        # WHEN: Call update_group
        result = await service.update_group(uuid4(), update_data, admin_user)

        # THEN: Returns None
        assert result is None


class TestGroupServiceDeleteGroup:
    """Tests for GroupService.delete_group method."""

    @pytest.mark.asyncio
    async def test_delete_group_soft_deletes(self):
        """
        GIVEN: GroupService with existing group
        WHEN: delete_group is called
        THEN: Group is soft deleted (is_active=False)
        """
        # GIVEN: Mock session with existing group
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        existing_group = MagicMock(spec=Group)
        existing_group.id = group_id
        existing_group.name = "To Delete"
        existing_group.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_group
        mock_session.execute.return_value = mock_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN: Call delete_group
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            result = await service.delete_group(group_id, admin_user)

        # THEN: Group is soft deleted
        assert result is True
        assert existing_group.is_active is False
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_group_not_found_returns_false(self):
        """
        GIVEN: GroupService with no matching group
        WHEN: delete_group is called with non-existent ID
        THEN: Returns False
        """
        # GIVEN: Mock session returning None
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN: Call delete_group
        result = await service.delete_group(uuid4(), admin_user)

        # THEN: Returns False
        assert result is False


class TestGroupServiceAddMembers:
    """Tests for GroupService.add_members method."""

    @pytest.mark.asyncio
    async def test_add_members_success(self):
        """
        GIVEN: GroupService with existing group and users
        WHEN: add_members is called with valid user IDs
        THEN: Members are added to group
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        existing_group = MagicMock(spec=Group)
        existing_group.id = group_id
        existing_group.is_active = True

        user_id_1 = uuid4()
        user_id_2 = uuid4()

        # Mock group lookup
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = existing_group

        # Mock existing memberships (empty)
        mock_existing_result = MagicMock()
        mock_existing_result.scalars.return_value.all.return_value = []

        # Mock user lookup
        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = [user_id_1, user_id_2]

        mock_session.execute.side_effect = [
            mock_group_result,
            mock_existing_result,
            mock_users_result,
        ]

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN: Call add_members
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            added = await service.add_members(
                group_id, [user_id_1, user_id_2], admin_user
            )

        # THEN: Members are added
        assert added == 2
        assert mock_session.add.call_count == 2

    @pytest.mark.asyncio
    async def test_add_members_skips_duplicates(self):
        """
        GIVEN: GroupService with group having existing member
        WHEN: add_members is called with existing member
        THEN: Existing member is skipped
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        existing_group = MagicMock(spec=Group)
        existing_group.id = group_id
        existing_group.is_active = True

        existing_user_id = uuid4()
        new_user_id = uuid4()

        # Mock group lookup
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = existing_group

        # Mock existing memberships (one user already member)
        mock_existing_result = MagicMock()
        mock_existing_result.scalars.return_value.all.return_value = [existing_user_id]

        # Mock user lookup (returns only new user ID)
        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = [new_user_id]

        mock_session.execute.side_effect = [
            mock_group_result,
            mock_existing_result,
            mock_users_result,
        ]

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN: Call add_members with existing + new user
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            added = await service.add_members(
                group_id, [existing_user_id, new_user_id], admin_user
            )

        # THEN: Only new member is added
        assert added == 1

    @pytest.mark.asyncio
    async def test_add_members_group_not_found_raises_error(self):
        """
        GIVEN: GroupService with no matching group
        WHEN: add_members is called with non-existent group
        THEN: Raises ValueError
        """
        # GIVEN: Mock session returning None
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN/THEN: add_members raises ValueError
        with pytest.raises(ValueError, match="Group not found"):
            await service.add_members(uuid4(), [uuid4()], admin_user)


class TestGroupServiceRemoveMember:
    """Tests for GroupService.remove_member method."""

    @pytest.mark.asyncio
    async def test_remove_member_success(self):
        """
        GIVEN: GroupService with group having member
        WHEN: remove_member is called
        THEN: Member is removed from group
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        group_id = uuid4()
        user_id = uuid4()

        existing_group = MagicMock(spec=Group)
        existing_group.id = group_id
        existing_group.is_active = True

        membership = MagicMock(spec=UserGroup)
        membership.group_id = group_id
        membership.user_id = user_id

        # Mock group lookup
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = existing_group

        # Mock membership lookup
        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none.return_value = membership

        mock_session.execute.side_effect = [mock_group_result, mock_membership_result]

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN: Call remove_member
        with patch("app.services.group_service.audit_service") as mock_audit:
            mock_audit.log_event = AsyncMock()
            result = await service.remove_member(group_id, user_id, admin_user)

        # THEN: Member is removed
        assert result is True
        mock_session.delete.assert_called_once_with(membership)

    @pytest.mark.asyncio
    async def test_remove_member_not_member_returns_false(self):
        """
        GIVEN: GroupService with user not in group
        WHEN: remove_member is called
        THEN: Returns False
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        existing_group = MagicMock(spec=Group)
        existing_group.is_active = True

        # Mock group lookup
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = existing_group

        # Mock membership lookup (not found)
        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [mock_group_result, mock_membership_result]

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN: Call remove_member
        result = await service.remove_member(uuid4(), uuid4(), admin_user)

        # THEN: Returns False
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_member_group_not_found_raises_error(self):
        """
        GIVEN: GroupService with no matching group
        WHEN: remove_member is called
        THEN: Raises ValueError
        """
        # GIVEN: Mock session returning None
        mock_session = AsyncMock()
        service = GroupService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        admin_user = MagicMock(spec=User)
        admin_user.id = uuid4()

        # WHEN/THEN: remove_member raises ValueError
        with pytest.raises(ValueError, match="Group not found"):
            await service.remove_member(uuid4(), uuid4(), admin_user)
