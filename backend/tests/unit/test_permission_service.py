"""Unit tests for PermissionService.

Story 7.11: Navigation Restructure with RBAC Default Groups

Test Coverage:
- [P0] get_user_permission_level: MAX aggregation across groups (AC-7.11.20)
- [P0] check_permission: Cumulative permission checks (AC-7.11.11)
- [P0] is_last_administrator: Safety check (AC-7.11.19)
- [P0] can_remove_from_administrators: Prevent removing last admin (AC-7.11.19)
- [P1] require_permission decorator: Endpoint protection (AC-7.11.11)

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- test-levels-framework.md: Unit test characteristics
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.permission_service import (
    PermissionLevel,
    PermissionService,
    require_permission,
)


class TestPermissionLevelEnum:
    """Tests for PermissionLevel enum values."""

    def test_user_level_is_1(self):
        """
        GIVEN: PermissionLevel enum
        WHEN: Accessing USER value
        THEN: Value is 1
        """
        assert PermissionLevel.USER == 1

    def test_operator_level_is_2(self):
        """
        GIVEN: PermissionLevel enum
        WHEN: Accessing OPERATOR value
        THEN: Value is 2
        """
        assert PermissionLevel.OPERATOR == 2

    def test_administrator_level_is_3(self):
        """
        GIVEN: PermissionLevel enum
        WHEN: Accessing ADMINISTRATOR value
        THEN: Value is 3
        """
        assert PermissionLevel.ADMINISTRATOR == 3

    def test_permission_levels_are_ordered(self):
        """
        GIVEN: PermissionLevel enum values
        WHEN: Comparing levels
        THEN: USER < OPERATOR < ADMINISTRATOR
        """
        assert PermissionLevel.USER < PermissionLevel.OPERATOR
        assert PermissionLevel.OPERATOR < PermissionLevel.ADMINISTRATOR


class TestGetUserPermissionLevel:
    """Tests for PermissionService.get_user_permission_level (AC-7.11.20)."""

    @pytest.mark.asyncio
    async def test_returns_max_level_from_multiple_groups(self):
        """
        GIVEN: User in multiple groups with different permission levels
        WHEN: get_user_permission_level is called
        THEN: Returns MAX permission_level across all groups (AC-7.11.20)
        """
        # GIVEN: Mock session returning MAX of 3 (Administrator)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3  # MAX level
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        # WHEN: Get permission level
        level = await service.get_user_permission_level(mock_user)

        # THEN: Returns max level
        assert level == PermissionLevel.ADMINISTRATOR
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_user_level_when_in_single_group(self):
        """
        GIVEN: User in only Users group (level 1)
        WHEN: get_user_permission_level is called
        THEN: Returns USER level (1)
        """
        # GIVEN: Mock session returning level 1
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        # WHEN: Get permission level
        level = await service.get_user_permission_level(mock_user)

        # THEN: Returns USER level
        assert level == PermissionLevel.USER

    @pytest.mark.asyncio
    async def test_returns_user_level_when_no_groups(self):
        """
        GIVEN: User not in any groups
        WHEN: get_user_permission_level is called
        THEN: Returns default USER level (1)
        """
        # GIVEN: Mock session returning None (no groups)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        # WHEN: Get permission level
        level = await service.get_user_permission_level(mock_user)

        # THEN: Returns default USER level
        assert level == PermissionLevel.USER

    @pytest.mark.asyncio
    async def test_superuser_fallback_when_not_in_groups(self):
        """
        GIVEN: User with is_superuser=True but not in any groups
        WHEN: get_user_permission_level is called
        THEN: Returns ADMINISTRATOR level (backwards compatibility)
        """
        # GIVEN: Mock session returning None (no groups)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = True  # Legacy superuser

        # WHEN: Get permission level
        level = await service.get_user_permission_level(mock_user)

        # THEN: Returns ADMINISTRATOR level as fallback
        assert level == PermissionLevel.ADMINISTRATOR


class TestCheckPermission:
    """Tests for PermissionService.check_permission (AC-7.11.11)."""

    @pytest.mark.asyncio
    async def test_admin_can_access_all_levels(self):
        """
        GIVEN: Administrator user (level 3)
        WHEN: Checking against any permission level
        THEN: Returns True for all levels (cumulative permissions)
        """
        # GIVEN: Mock service returning ADMINISTRATOR level
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        # WHEN/THEN: Check all levels - all should pass
        assert await service.check_permission(mock_user, PermissionLevel.USER) is True
        assert (
            await service.check_permission(mock_user, PermissionLevel.OPERATOR) is True
        )
        assert (
            await service.check_permission(mock_user, PermissionLevel.ADMINISTRATOR)
            is True
        )

    @pytest.mark.asyncio
    async def test_operator_can_access_user_and_operator_levels(self):
        """
        GIVEN: Operator user (level 2)
        WHEN: Checking against USER or OPERATOR levels
        THEN: Returns True (cumulative permissions)
        """
        # GIVEN: Mock service returning OPERATOR level
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        # WHEN/THEN: Check USER and OPERATOR levels - should pass
        assert await service.check_permission(mock_user, PermissionLevel.USER) is True
        assert (
            await service.check_permission(mock_user, PermissionLevel.OPERATOR) is True
        )

    @pytest.mark.asyncio
    async def test_operator_cannot_access_admin_level(self):
        """
        GIVEN: Operator user (level 2)
        WHEN: Checking against ADMINISTRATOR level
        THEN: Returns False
        """
        # GIVEN: Mock service returning OPERATOR level
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        # WHEN/THEN: Check ADMINISTRATOR level - should fail
        assert (
            await service.check_permission(mock_user, PermissionLevel.ADMINISTRATOR)
            is False
        )

    @pytest.mark.asyncio
    async def test_basic_user_can_only_access_user_level(self):
        """
        GIVEN: Basic user (level 1)
        WHEN: Checking against OPERATOR or ADMINISTRATOR levels
        THEN: Returns False
        """
        # GIVEN: Mock service returning USER level
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        # WHEN/THEN: Check USER level - should pass
        assert await service.check_permission(mock_user, PermissionLevel.USER) is True

        # Reset mock for next calls
        mock_session.execute.return_value = mock_result

        # WHEN/THEN: Check higher levels - should fail
        assert (
            await service.check_permission(mock_user, PermissionLevel.OPERATOR) is False
        )

        mock_session.execute.return_value = mock_result
        assert (
            await service.check_permission(mock_user, PermissionLevel.ADMINISTRATOR)
            is False
        )


class TestIsLastAdministrator:
    """Tests for PermissionService.is_last_administrator (AC-7.11.19)."""

    @pytest.mark.asyncio
    async def test_returns_true_when_only_admin(self):
        """
        GIVEN: User is the only member of Administrators group
        WHEN: is_last_administrator is called
        THEN: Returns True
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        user_id = uuid4()
        admin_group_id = uuid4()

        # Mock get_administrators_group_id
        mock_admin_group_result = MagicMock()
        mock_admin_group_result.scalar_one_or_none.return_value = admin_group_id

        # Mock check if user is in admin group
        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none.return_value = (
            MagicMock()
        )  # User is in group

        # Mock count_administrators (returns 1)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_session.execute.side_effect = [
            mock_admin_group_result,
            mock_membership_result,
            mock_count_result,
        ]

        service = PermissionService(mock_session)

        # WHEN: Check if last admin
        result = await service.is_last_administrator(user_id)

        # THEN: Returns True
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_multiple_admins(self):
        """
        GIVEN: Multiple users in Administrators group
        WHEN: is_last_administrator is called
        THEN: Returns False
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        user_id = uuid4()
        admin_group_id = uuid4()

        # Mock get_administrators_group_id
        mock_admin_group_result = MagicMock()
        mock_admin_group_result.scalar_one_or_none.return_value = admin_group_id

        # Mock check if user is in admin group
        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none.return_value = MagicMock()

        # Mock count_administrators (returns 3)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3

        mock_session.execute.side_effect = [
            mock_admin_group_result,
            mock_membership_result,
            mock_count_result,
        ]

        service = PermissionService(mock_session)

        # WHEN: Check if last admin
        result = await service.is_last_administrator(user_id)

        # THEN: Returns False
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_user_not_admin(self):
        """
        GIVEN: User not in Administrators group
        WHEN: is_last_administrator is called
        THEN: Returns False
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        user_id = uuid4()
        admin_group_id = uuid4()

        # Mock get_administrators_group_id
        mock_admin_group_result = MagicMock()
        mock_admin_group_result.scalar_one_or_none.return_value = admin_group_id

        # Mock check if user is in admin group (not in group)
        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            mock_admin_group_result,
            mock_membership_result,
        ]

        service = PermissionService(mock_session)

        # WHEN: Check if last admin
        result = await service.is_last_administrator(user_id)

        # THEN: Returns False
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_admin_group(self):
        """
        GIVEN: Administrators group doesn't exist
        WHEN: is_last_administrator is called
        THEN: Returns False
        """
        # GIVEN: Mock session returning no admin group
        mock_session = AsyncMock()
        user_id = uuid4()

        mock_admin_group_result = MagicMock()
        mock_admin_group_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = mock_admin_group_result

        service = PermissionService(mock_session)

        # WHEN: Check if last admin
        result = await service.is_last_administrator(user_id)

        # THEN: Returns False
        assert result is False


class TestCanRemoveFromAdministrators:
    """Tests for PermissionService.can_remove_from_administrators (AC-7.11.19)."""

    @pytest.mark.asyncio
    async def test_blocks_removal_of_last_admin(self):
        """
        GIVEN: User is the last administrator
        WHEN: can_remove_from_administrators is called
        THEN: Returns (False, error message)
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        user_id = uuid4()
        admin_group_id = uuid4()

        # Mock get_administrators_group_id (first call)
        mock_admin_group_result1 = MagicMock()
        mock_admin_group_result1.scalar_one_or_none.return_value = admin_group_id

        # Mock is_last_administrator chain
        mock_admin_group_result2 = MagicMock()
        mock_admin_group_result2.scalar_one_or_none.return_value = admin_group_id

        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none.return_value = MagicMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1  # Only admin

        mock_session.execute.side_effect = [
            mock_admin_group_result1,
            mock_admin_group_result2,
            mock_membership_result,
            mock_count_result,
        ]

        service = PermissionService(mock_session)

        # WHEN: Check if can remove
        can_remove, error = await service.can_remove_from_administrators(
            user_id, admin_group_id
        )

        # THEN: Removal is blocked
        assert can_remove is False
        assert error == "Cannot remove the last administrator"

    @pytest.mark.asyncio
    async def test_allows_removal_when_multiple_admins(self):
        """
        GIVEN: Multiple administrators exist
        WHEN: can_remove_from_administrators is called
        THEN: Returns (True, None)
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        user_id = uuid4()
        admin_group_id = uuid4()

        # Mock get_administrators_group_id
        mock_admin_group_result1 = MagicMock()
        mock_admin_group_result1.scalar_one_or_none.return_value = admin_group_id

        # Mock is_last_administrator returns False
        mock_admin_group_result2 = MagicMock()
        mock_admin_group_result2.scalar_one_or_none.return_value = admin_group_id

        mock_membership_result = MagicMock()
        mock_membership_result.scalar_one_or_none.return_value = MagicMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3  # Multiple admins

        mock_session.execute.side_effect = [
            mock_admin_group_result1,
            mock_admin_group_result2,
            mock_membership_result,
            mock_count_result,
        ]

        service = PermissionService(mock_session)

        # WHEN: Check if can remove
        can_remove, error = await service.can_remove_from_administrators(
            user_id, admin_group_id
        )

        # THEN: Removal is allowed
        assert can_remove is True
        assert error is None

    @pytest.mark.asyncio
    async def test_allows_removal_from_non_admin_group(self):
        """
        GIVEN: Removing from a non-admin group
        WHEN: can_remove_from_administrators is called
        THEN: Returns (True, None) - no restriction
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        user_id = uuid4()
        regular_group_id = uuid4()
        admin_group_id = uuid4()

        # Mock get_administrators_group_id
        mock_admin_group_result = MagicMock()
        mock_admin_group_result.scalar_one_or_none.return_value = admin_group_id

        mock_session.execute.return_value = mock_admin_group_result

        service = PermissionService(mock_session)

        # WHEN: Check if can remove from different group
        can_remove, error = await service.can_remove_from_administrators(
            user_id, regular_group_id
        )

        # THEN: Removal is allowed (not admin group)
        assert can_remove is True
        assert error is None


class TestCountAdministrators:
    """Tests for PermissionService.count_administrators."""

    @pytest.mark.asyncio
    async def test_returns_correct_count(self):
        """
        GIVEN: Administrators group with members
        WHEN: count_administrators is called
        THEN: Returns correct count
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)

        # WHEN: Count admins
        count = await service.count_administrators()

        # THEN: Returns correct count
        assert count == 5

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_admins(self):
        """
        GIVEN: No users in Administrators group
        WHEN: count_administrators is called
        THEN: Returns 0
        """
        # GIVEN: Mock session returning None/0
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        service = PermissionService(mock_session)

        # WHEN: Count admins
        count = await service.count_administrators()

        # THEN: Returns 0
        assert count == 0


class TestRequirePermissionDecorator:
    """Tests for require_permission decorator (AC-7.11.11)."""

    @pytest.mark.asyncio
    async def test_decorator_allows_sufficient_permission(self):
        """
        GIVEN: User with sufficient permission level
        WHEN: Decorated function is called
        THEN: Function executes normally
        """

        # GIVEN: Mock decorated function
        @require_permission(PermissionLevel.OPERATOR)
        async def protected_endpoint(current_user, session):
            return {"status": "success"}

        # Mock user and session
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2  # OPERATOR level
        mock_session.execute.return_value = mock_result

        # WHEN: Call the decorated function
        result = await protected_endpoint(current_user=mock_user, session=mock_session)

        # THEN: Function executes
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_decorator_blocks_insufficient_permission(self):
        """
        GIVEN: User with insufficient permission level
        WHEN: Decorated function is called
        THEN: Raises 403 HTTPException
        """
        from fastapi import HTTPException

        # GIVEN: Mock decorated function
        @require_permission(PermissionLevel.ADMINISTRATOR)
        async def admin_endpoint(current_user, session):
            return {"status": "success"}

        # Mock user and session
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1  # USER level (insufficient)
        mock_session.execute.return_value = mock_result

        # WHEN/THEN: Call raises HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await admin_endpoint(current_user=mock_user, session=mock_session)

        assert exc_info.value.status_code == 403
        assert "ADMINISTRATOR" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_decorator_raises_401_without_user(self):
        """
        GIVEN: No current_user in kwargs
        WHEN: Decorated function is called
        THEN: Raises 401 HTTPException
        """
        from fastapi import HTTPException

        # GIVEN: Mock decorated function
        @require_permission(PermissionLevel.USER)
        async def protected_endpoint(current_user=None, session=None):
            return {"status": "success"}

        mock_session = AsyncMock()

        # WHEN/THEN: Call raises HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(session=mock_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_decorator_raises_500_without_session(self):
        """
        GIVEN: No session in kwargs
        WHEN: Decorated function is called
        THEN: Raises 500 HTTPException
        """
        from fastapi import HTTPException

        # GIVEN: Mock decorated function
        @require_permission(PermissionLevel.USER)
        async def protected_endpoint(current_user, session=None):
            return {"status": "success"}

        mock_user = MagicMock()
        mock_user.id = uuid4()

        # WHEN/THEN: Call raises HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(current_user=mock_user)

        assert exc_info.value.status_code == 500
