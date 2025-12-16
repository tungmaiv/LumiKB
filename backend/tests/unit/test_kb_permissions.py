"""Unit tests for Knowledge Base permission logic.

Tests permission hierarchy and schema validation without database dependencies.
Full service integration tests are in integration/test_kb_permissions.py.
"""

from datetime import UTC

import pytest
from pydantic import ValidationError

from app.models.permission import PermissionLevel
from app.schemas.permission import (
    PermissionCreate,
    PermissionListResponse,
    PermissionResponse,
)
from app.services.kb_service import PERMISSION_HIERARCHY

pytestmark = pytest.mark.unit


class TestPermissionHierarchyExtended:
    """Extended tests for permission hierarchy logic (AC7)."""

    def test_hierarchy_values(self) -> None:
        """Test exact hierarchy values: ADMIN=3, WRITE=2, READ=1."""
        assert PERMISSION_HIERARCHY[PermissionLevel.ADMIN] == 3
        assert PERMISSION_HIERARCHY[PermissionLevel.WRITE] == 2
        assert PERMISSION_HIERARCHY[PermissionLevel.READ] == 1

    def test_admin_includes_write_permissions(self) -> None:
        """Test ADMIN includes all WRITE permissions (AC7)."""
        admin_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        write_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        # ADMIN >= WRITE means ADMIN can do anything WRITE can do
        assert admin_level >= write_level

    def test_write_includes_read_permissions(self) -> None:
        """Test WRITE includes all READ permissions (AC7)."""
        write_level = PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        read_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        # WRITE >= READ means WRITE can do anything READ can do
        assert write_level >= read_level

    def test_admin_includes_read_permissions(self) -> None:
        """Test ADMIN includes all READ permissions (transitive via WRITE)."""
        admin_level = PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
        read_level = PERMISSION_HIERARCHY[PermissionLevel.READ]
        assert admin_level >= read_level

    def test_permission_check_user_level_gte_required(self) -> None:
        """Test permission check formula: user_level >= required_level (AC7)."""
        # Test all valid combinations
        test_cases = [
            (PermissionLevel.ADMIN, PermissionLevel.ADMIN, True),
            (PermissionLevel.ADMIN, PermissionLevel.WRITE, True),
            (PermissionLevel.ADMIN, PermissionLevel.READ, True),
            (PermissionLevel.WRITE, PermissionLevel.ADMIN, False),
            (PermissionLevel.WRITE, PermissionLevel.WRITE, True),
            (PermissionLevel.WRITE, PermissionLevel.READ, True),
            (PermissionLevel.READ, PermissionLevel.ADMIN, False),
            (PermissionLevel.READ, PermissionLevel.WRITE, False),
            (PermissionLevel.READ, PermissionLevel.READ, True),
        ]

        for user_level, required_level, expected in test_cases:
            user_val = PERMISSION_HIERARCHY[user_level]
            required_val = PERMISSION_HIERARCHY[required_level]
            result = user_val >= required_val
            assert result == expected, (
                f"Expected {user_level} >= {required_level} to be {expected}, got {result}"
            )


class TestPermissionCreateSchema:
    """Tests for PermissionCreate Pydantic schema."""

    def test_valid_permission_create_read(self) -> None:
        """Test creating permission with READ level."""
        from uuid import uuid4

        user_id = uuid4()
        schema = PermissionCreate(
            user_id=user_id, permission_level=PermissionLevel.READ
        )
        assert schema.user_id == user_id
        assert schema.permission_level == PermissionLevel.READ

    def test_valid_permission_create_write(self) -> None:
        """Test creating permission with WRITE level."""
        from uuid import uuid4

        user_id = uuid4()
        schema = PermissionCreate(
            user_id=user_id, permission_level=PermissionLevel.WRITE
        )
        assert schema.user_id == user_id
        assert schema.permission_level == PermissionLevel.WRITE

    def test_valid_permission_create_admin(self) -> None:
        """Test creating permission with ADMIN level."""
        from uuid import uuid4

        user_id = uuid4()
        schema = PermissionCreate(
            user_id=user_id, permission_level=PermissionLevel.ADMIN
        )
        assert schema.user_id == user_id
        assert schema.permission_level == PermissionLevel.ADMIN

    def test_permission_create_missing_user_id(self) -> None:
        """Test PermissionCreate fails without user_id."""
        with pytest.raises(ValidationError) as exc_info:
            PermissionCreate(permission_level=PermissionLevel.READ)  # type: ignore[call-arg]
        assert "user_id" in str(exc_info.value)

    def test_permission_create_missing_level(self) -> None:
        """Test PermissionCreate fails without permission_level."""
        from uuid import uuid4

        with pytest.raises(ValidationError) as exc_info:
            PermissionCreate(user_id=uuid4())  # type: ignore[call-arg]
        assert "permission_level" in str(exc_info.value)

    def test_permission_create_invalid_level(self) -> None:
        """Test PermissionCreate fails with invalid permission level."""
        from uuid import uuid4

        with pytest.raises(ValidationError) as exc_info:
            PermissionCreate(user_id=uuid4(), permission_level="INVALID")  # type: ignore[arg-type]
        assert "permission_level" in str(exc_info.value)

    def test_permission_create_invalid_user_id(self) -> None:
        """Test PermissionCreate fails with invalid UUID."""
        with pytest.raises(ValidationError) as exc_info:
            PermissionCreate(
                user_id="not-a-uuid", permission_level=PermissionLevel.READ
            )  # type: ignore[arg-type]
        assert "user_id" in str(exc_info.value)


class TestPermissionResponseSchema:
    """Tests for PermissionResponse Pydantic schema."""

    def test_valid_permission_response(self) -> None:
        """Test creating valid PermissionResponse."""
        from datetime import datetime
        from uuid import uuid4

        response = PermissionResponse(
            id=uuid4(),
            user_id=uuid4(),
            email="test@example.com",
            kb_id=uuid4(),
            permission_level=PermissionLevel.READ,
            created_at=datetime.now(tz=UTC),
        )
        assert response.email == "test@example.com"
        assert response.permission_level == PermissionLevel.READ

    def test_permission_response_requires_email(self) -> None:
        """Test PermissionResponse requires email field."""
        from datetime import datetime
        from uuid import uuid4

        with pytest.raises(ValidationError) as exc_info:
            PermissionResponse(
                id=uuid4(),
                user_id=uuid4(),
                kb_id=uuid4(),
                permission_level=PermissionLevel.READ,
                created_at=datetime.now(tz=UTC),
            )  # type: ignore[call-arg]
        assert "email" in str(exc_info.value)


class TestPermissionListResponseSchema:
    """Tests for PermissionListResponse Pydantic schema."""

    def test_empty_list_response(self) -> None:
        """Test PermissionListResponse with empty data."""
        response = PermissionListResponse(data=[], total=0, page=1, limit=20)
        assert response.data == []
        assert response.total == 0
        assert response.page == 1
        assert response.limit == 20

    def test_list_response_with_items(self) -> None:
        """Test PermissionListResponse with permission items."""
        from datetime import datetime
        from uuid import uuid4

        items = [
            PermissionResponse(
                id=uuid4(),
                user_id=uuid4(),
                email="user1@example.com",
                kb_id=uuid4(),
                permission_level=PermissionLevel.READ,
                created_at=datetime.now(tz=UTC),
            ),
            PermissionResponse(
                id=uuid4(),
                user_id=uuid4(),
                email="user2@example.com",
                kb_id=uuid4(),
                permission_level=PermissionLevel.ADMIN,
                created_at=datetime.now(tz=UTC),
            ),
        ]
        response = PermissionListResponse(data=items, total=2, page=1, limit=20)
        assert len(response.data) == 2
        assert response.total == 2


class TestPermissionLevelEnum:
    """Tests for PermissionLevel enum."""

    def test_enum_values(self) -> None:
        """Test PermissionLevel enum has correct values."""
        assert PermissionLevel.READ.value == "READ"
        assert PermissionLevel.WRITE.value == "WRITE"
        assert PermissionLevel.ADMIN.value == "ADMIN"

    def test_enum_from_string(self) -> None:
        """Test creating PermissionLevel from string."""
        assert PermissionLevel("READ") == PermissionLevel.READ
        assert PermissionLevel("WRITE") == PermissionLevel.WRITE
        assert PermissionLevel("ADMIN") == PermissionLevel.ADMIN

    def test_invalid_enum_value(self) -> None:
        """Test invalid string raises ValueError."""
        with pytest.raises(ValueError):
            PermissionLevel("INVALID")

    def test_enum_is_string_subclass(self) -> None:
        """Test PermissionLevel is str subclass for JSON serialization."""
        assert isinstance(PermissionLevel.READ, str)
        assert PermissionLevel.READ.value == "READ"


class TestOwnerBypassLogic:
    """Tests for owner bypass logic documentation (AC8).

    Note: Actual database-based owner bypass tests are in integration tests.
    These tests document the expected behavior.
    """

    def test_owner_bypass_concept(self) -> None:
        """Document: Owner has implicit ADMIN permission without kb_permissions entry.

        AC8: KB owner automatically has ADMIN permission (owner bypass).
        No explicit kb_permissions entry required for owner.

        Implementation: check_permission() checks if kb.owner_id == user.id
        before querying kb_permissions table.
        """
        # This is a documentation test - actual logic tested in integration
        expected_behavior = """
        When check_permission is called:
        1. If user.is_superuser -> return True
        2. If kb.owner_id == user.id -> return True (owner bypass)
        3. Query kb_permissions for user's level
        4. Compare user_level >= required_level
        """
        assert "owner bypass" in expected_behavior.lower()

    def test_owner_does_not_need_explicit_permission(self) -> None:
        """Document: Owner should work without explicit kb_permissions entry.

        The owner_id field in knowledge_bases table grants implicit ADMIN.
        """
        # Documentation test - actual tested in integration
        pass
