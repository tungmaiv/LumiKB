"""Unit tests for Knowledge Base Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.models.permission import PermissionLevel
from app.schemas.knowledge_base import KBCreate, KBUpdate

pytestmark = pytest.mark.unit


class TestKBCreate:
    """Tests for KBCreate schema validation."""

    def test_valid_name_only(self) -> None:
        """Test creating KB with only required name field."""
        schema = KBCreate(name="Test KB")
        assert schema.name == "Test KB"
        assert schema.description is None

    def test_valid_name_and_description(self) -> None:
        """Test creating KB with name and description."""
        schema = KBCreate(name="Test KB", description="A test knowledge base")
        assert schema.name == "Test KB"
        assert schema.description == "A test knowledge base"

    def test_name_min_length(self) -> None:
        """Test that name must be at least 1 character."""
        # Empty string should fail
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_name_max_length(self) -> None:
        """Test that name cannot exceed 255 characters."""
        # 256 characters should fail
        long_name = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name=long_name)
        assert "String should have at most 255 characters" in str(exc_info.value)

    def test_name_exactly_255_chars(self) -> None:
        """Test that name can be exactly 255 characters."""
        name_255 = "a" * 255
        schema = KBCreate(name=name_255)
        assert len(schema.name) == 255

    def test_description_max_length(self) -> None:
        """Test that description cannot exceed 2000 characters."""
        # 2001 characters should fail
        long_desc = "a" * 2001
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test", description=long_desc)
        assert "String should have at most 2000 characters" in str(exc_info.value)

    def test_description_exactly_2000_chars(self) -> None:
        """Test that description can be exactly 2000 characters."""
        desc_2000 = "a" * 2000
        schema = KBCreate(name="Test", description=desc_2000)
        assert len(schema.description) == 2000

    def test_name_required(self) -> None:
        """Test that name is a required field."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate()  # type: ignore
        assert "Field required" in str(exc_info.value)


class TestKBUpdate:
    """Tests for KBUpdate schema validation."""

    def test_all_fields_optional(self) -> None:
        """Test that all fields are optional for updates."""
        schema = KBUpdate()
        assert schema.name is None
        assert schema.description is None

    def test_update_name_only(self) -> None:
        """Test updating only name."""
        schema = KBUpdate(name="New Name")
        assert schema.name == "New Name"
        assert schema.description is None

    def test_update_description_only(self) -> None:
        """Test updating only description."""
        schema = KBUpdate(description="New description")
        assert schema.name is None
        assert schema.description == "New description"

    def test_update_both_fields(self) -> None:
        """Test updating both name and description."""
        schema = KBUpdate(name="New Name", description="New description")
        assert schema.name == "New Name"
        assert schema.description == "New description"

    def test_name_min_length_if_provided(self) -> None:
        """Test that name must be at least 1 char if provided."""
        with pytest.raises(ValidationError) as exc_info:
            KBUpdate(name="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_name_max_length_if_provided(self) -> None:
        """Test that name cannot exceed 255 chars if provided."""
        with pytest.raises(ValidationError) as exc_info:
            KBUpdate(name="a" * 256)
        assert "String should have at most 255 characters" in str(exc_info.value)

    def test_description_max_length_if_provided(self) -> None:
        """Test that description cannot exceed 2000 chars if provided."""
        with pytest.raises(ValidationError) as exc_info:
            KBUpdate(description="a" * 2001)
        assert "String should have at most 2000 characters" in str(exc_info.value)


class TestPermissionHierarchy:
    """Tests for permission level hierarchy logic."""

    def test_permission_level_enum_values(self) -> None:
        """Test that PermissionLevel enum has correct values."""
        assert PermissionLevel.READ.value == "READ"
        assert PermissionLevel.WRITE.value == "WRITE"
        assert PermissionLevel.ADMIN.value == "ADMIN"

    def test_permission_level_from_string(self) -> None:
        """Test creating PermissionLevel from string."""
        assert PermissionLevel("READ") == PermissionLevel.READ
        assert PermissionLevel("WRITE") == PermissionLevel.WRITE
        assert PermissionLevel("ADMIN") == PermissionLevel.ADMIN

    def test_permission_level_ordering(self) -> None:
        """Test that permission hierarchy is correct conceptually.

        ADMIN > WRITE > READ
        This is tested via the PERMISSION_HIERARCHY dict in kb_service.
        """
        from app.services.kb_service import PERMISSION_HIERARCHY

        assert (
            PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
            > PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        )
        assert (
            PERMISSION_HIERARCHY[PermissionLevel.WRITE]
            > PERMISSION_HIERARCHY[PermissionLevel.READ]
        )
        assert (
            PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
            > PERMISSION_HIERARCHY[PermissionLevel.READ]
        )
