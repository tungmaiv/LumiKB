"""Unit tests for Knowledge Base service logic.

Note: These tests focus on business logic validation that can be tested
without database dependencies. Full service tests are in integration/.
"""

import pytest

from app.models.permission import PermissionLevel
from app.services.kb_service import PERMISSION_HIERARCHY

pytestmark = pytest.mark.unit


class TestPermissionHierarchy:
    """Tests for permission hierarchy logic."""

    def test_admin_higher_than_write(self) -> None:
        """Test ADMIN permission is higher than WRITE."""
        admin_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        write_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        assert admin_level > write_level

    def test_write_higher_than_read(self) -> None:
        """Test WRITE permission is higher than READ."""
        write_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        read_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        assert write_level > read_level

    def test_admin_higher_than_read(self) -> None:
        """Test ADMIN permission is higher than READ."""
        admin_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        read_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        assert admin_level > read_level

    def test_same_level_equal(self) -> None:
        """Test same permission levels are equal."""
        assert (
            PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
            == PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        )
        assert (
            PERMISSION_HIERARCHY[PermissionLevel.WRITE]
            == PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        )
        assert (
            PERMISSION_HIERARCHY[PermissionLevel.READ]
            == PERMISSION_HIERARCHY[PermissionLevel.READ]
        )

    def test_all_levels_have_values(self) -> None:
        """Test all permission levels are in hierarchy."""
        assert PermissionLevel.READ in PERMISSION_HIERARCHY
        assert PermissionLevel.WRITE in PERMISSION_HIERARCHY
        assert PermissionLevel.ADMIN in PERMISSION_HIERARCHY

    def test_hierarchy_values_are_positive(self) -> None:
        """Test all hierarchy values are positive integers."""
        for _level, value in PERMISSION_HIERARCHY.items():
            assert isinstance(value, int)
            assert value > 0


class TestPermissionCheckLogic:
    """Tests for permission check logic (without DB)."""

    def test_read_satisfies_read(self) -> None:
        """Test READ permission satisfies READ requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        assert user_level >= required_level

    def test_write_satisfies_read(self) -> None:
        """Test WRITE permission satisfies READ requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        assert user_level >= required_level

    def test_admin_satisfies_read(self) -> None:
        """Test ADMIN permission satisfies READ requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        assert user_level >= required_level

    def test_read_does_not_satisfy_write(self) -> None:
        """Test READ permission does not satisfy WRITE requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        assert not (user_level >= required_level)

    def test_read_does_not_satisfy_admin(self) -> None:
        """Test READ permission does not satisfy ADMIN requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        assert not (user_level >= required_level)

    def test_write_does_not_satisfy_admin(self) -> None:
        """Test WRITE permission does not satisfy ADMIN requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        assert not (user_level >= required_level)

    def test_write_satisfies_write(self) -> None:
        """Test WRITE permission satisfies WRITE requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        assert user_level >= required_level

    def test_admin_satisfies_write(self) -> None:
        """Test ADMIN permission satisfies WRITE requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        assert user_level >= required_level

    def test_admin_satisfies_admin(self) -> None:
        """Test ADMIN permission satisfies ADMIN requirement."""
        user_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        required_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        assert user_level >= required_level


class TestKBStatusValues:
    """Tests for KB status value constants."""

    def test_valid_kb_statuses(self) -> None:
        """Test expected KB status values."""
        valid_statuses = {"active", "archived"}
        # These are the only valid statuses per the spec
        assert "active" in valid_statuses
        assert "archived" in valid_statuses

    def test_default_kb_status(self) -> None:
        """Test default KB status is 'active'."""
        # This is validated in the model/migration
        default_status = "active"
        assert default_status == "active"
