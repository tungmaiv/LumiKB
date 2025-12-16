"""Unit tests for audit event type and resource type enums."""

import pytest
from pydantic import ValidationError

from app.schemas.admin import (
    AuditEventType,
    AuditLogFilterRequest,
    AuditResourceType,
)


def test_event_type_enum_validation():
    """Test that event_type accepts valid enum values."""
    # Valid event types
    valid_types = [
        "search",
        "generation.request",
        "generation.complete",
        "generation.failed",
        "document.uploaded",
        "kb.updated",
    ]

    for event_type in valid_types:
        request = AuditLogFilterRequest(event_type=event_type)
        assert request.event_type.value == event_type

    # Invalid event type should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        AuditLogFilterRequest(event_type="invalid_event_type")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "enum"
    assert "event_type" in str(errors[0]["loc"])


def test_resource_type_enum_validation():
    """Test that resource_type accepts valid enum values."""
    # Valid resource types
    valid_types = ["document", "knowledge_base", "draft", "search", "user"]

    for resource_type in valid_types:
        request = AuditLogFilterRequest(resource_type=resource_type)
        assert request.resource_type.value == resource_type

    # Invalid resource type should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        AuditLogFilterRequest(resource_type="invalid_resource_type")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "enum"
    assert "resource_type" in str(errors[0]["loc"])


def test_enum_values_optional():
    """Test that event_type and resource_type are optional fields."""
    # Should work without event_type or resource_type
    request = AuditLogFilterRequest()
    assert request.event_type is None
    assert request.resource_type is None

    # Should work with only one filter
    request_with_event = AuditLogFilterRequest(event_type="search")
    assert request_with_event.event_type == AuditEventType.SEARCH
    assert request_with_event.resource_type is None

    request_with_resource = AuditLogFilterRequest(resource_type="document")
    assert request_with_resource.event_type is None
    assert request_with_resource.resource_type == AuditResourceType.DOCUMENT


def test_enum_string_conversion():
    """Test that enum values convert to strings correctly."""
    request = AuditLogFilterRequest(
        event_type="generation.request", resource_type="draft"
    )

    # Enums should be accessible as enum values
    assert request.event_type == AuditEventType.GENERATION_REQUEST
    assert request.resource_type == AuditResourceType.DRAFT

    # Enums should convert to strings via .value
    assert request.event_type.value == "generation.request"
    assert request.resource_type.value == "draft"


def test_all_event_types_defined():
    """Test that all expected event types are defined in the enum."""
    expected_event_types = {
        "search",
        "generation.request",
        "generation.complete",
        "generation.failed",
        "generation.feedback",
        "document.uploaded",
        "document.retry",
        "document.deleted",
        "document.replaced",
        "document.export",
        "kb.created",
        "kb.updated",
        "kb.archived",
        "kb.permission_granted",
        "kb.permission_revoked",
        "user.login",
        "user.logout",
        "user.login_failed",
        "change_search",
        "add_context",
        "new_draft",
        "select_template",
        "regenerate_with_structure",
        "regenerate_detailed",
        "add_sections",
        "search_better_sources",
        "review_citations",
        "regenerate_with_feedback",
        "adjust_parameters",
    }

    actual_event_types = {e.value for e in AuditEventType}
    assert actual_event_types == expected_event_types


def test_all_resource_types_defined():
    """Test that all expected resource types are defined in the enum."""
    expected_resource_types = {
        "document",
        "knowledge_base",
        "draft",
        "search",
        "user",
    }

    actual_resource_types = {r.value for r in AuditResourceType}
    assert actual_resource_types == expected_resource_types
