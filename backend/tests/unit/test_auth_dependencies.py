"""Unit tests for auth.py dependencies.

Story 7-27: Queue Monitoring Enhancement with Operator Access
- AC-7.27.16: Operator (level >= 2) can access queue monitoring
- AC-7.27.17: Regular user (level = 1) denied
- AC-7.27.18: Superuser always has access
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.auth import get_current_operator_or_admin
from app.services.permission_service import PermissionLevel


class TestGetCurrentOperatorOrAdmin:
    """Tests for get_current_operator_or_admin dependency (Story 7-27 AC-7.27.16-18)."""

    @pytest.mark.asyncio
    async def test_superuser_always_has_access(self) -> None:
        """AC-7.27.18: Superuser is granted access regardless of group membership.

        Given a user with is_superuser=True
        When get_current_operator_or_admin is called
        Then access is granted (user returned)
        """
        # Given
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = True
        mock_session = AsyncMock()

        # When
        result = await get_current_operator_or_admin(
            user=mock_user,
            session=mock_session,
        )

        # Then
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_operator_level_has_access(self) -> None:
        """AC-7.27.16: User with permission_level >= 2 can access queue monitoring.

        Given a non-superuser user in a group with permission_level = 2
        When get_current_operator_or_admin is called
        Then access is granted (user returned)
        """
        # Given
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False
        mock_session = AsyncMock()

        # Patch where PermissionService is imported in auth.py (late import)
        with patch(
            "app.services.permission_service.PermissionService"
        ) as mock_permission_service_class:
            mock_service = MagicMock()
            mock_service.check_permission = AsyncMock(return_value=True)
            mock_permission_service_class.return_value = mock_service

            # When
            result = await get_current_operator_or_admin(
                user=mock_user,
                session=mock_session,
            )

            # Then
            assert result == mock_user
            mock_service.check_permission.assert_called_once_with(
                mock_user, PermissionLevel.OPERATOR
            )

    @pytest.mark.asyncio
    async def test_administrator_level_has_access(self) -> None:
        """AC-7.27.16: User with permission_level = 3 can access queue monitoring.

        Given a non-superuser user in a group with permission_level = 3
        When get_current_operator_or_admin is called
        Then access is granted (user returned)
        """
        # Given
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False
        mock_session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionService"
        ) as mock_permission_service_class:
            mock_service = MagicMock()
            # Administrator level (3) passes OPERATOR (2) check
            mock_service.check_permission = AsyncMock(return_value=True)
            mock_permission_service_class.return_value = mock_service

            # When
            result = await get_current_operator_or_admin(
                user=mock_user,
                session=mock_session,
            )

            # Then
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_regular_user_denied_access(self) -> None:
        """AC-7.27.17: User with permission_level = 1 is denied access.

        Given a non-superuser user in a group with permission_level = 1
        When get_current_operator_or_admin is called
        Then access is denied (403 Forbidden)
        """
        # Given
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False
        mock_session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionService"
        ) as mock_permission_service_class:
            mock_service = MagicMock()
            # Regular user (level 1) fails OPERATOR (2) check
            mock_service.check_permission = AsyncMock(return_value=False)
            mock_permission_service_class.return_value = mock_service

            # When / Then
            with pytest.raises(HTTPException) as exc_info:
                await get_current_operator_or_admin(
                    user=mock_user,
                    session=mock_session,
                )

            assert exc_info.value.status_code == 403
            assert "Operator permission" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_user_with_no_groups_denied_access(self) -> None:
        """AC-7.27.17: User with no group membership is denied access.

        Given a non-superuser user not in any group
        When get_current_operator_or_admin is called
        Then access is denied (403 Forbidden)
        """
        # Given
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.is_superuser = False
        mock_session = AsyncMock()

        with patch(
            "app.services.permission_service.PermissionService"
        ) as mock_permission_service_class:
            mock_service = MagicMock()
            # User with no groups defaults to level 1, fails check
            mock_service.check_permission = AsyncMock(return_value=False)
            mock_permission_service_class.return_value = mock_service

            # When / Then
            with pytest.raises(HTTPException) as exc_info:
                await get_current_operator_or_admin(
                    user=mock_user,
                    session=mock_session,
                )

            assert exc_info.value.status_code == 403
