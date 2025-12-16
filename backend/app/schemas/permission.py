"""Permission Pydantic schemas for Knowledge Base access control.

Story 5.20: Extended with group permission support (AC-5.20.5)
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.permission import PermissionLevel


# Request schemas
class PermissionCreate(BaseModel):
    """Request schema for granting permission to a user on a KB.

    AC1: POST /api/v1/knowledge-bases/{id}/permissions request body.
    """

    user_id: UUID = Field(..., description="UUID of the user to grant permission to")
    permission_level: PermissionLevel = Field(
        ..., description="Permission level to grant (READ, WRITE, ADMIN)"
    )


class PermissionCreateExtended(BaseModel):
    """Extended request schema for granting permission to a user OR group.

    Story 5.20 (AC-5.20.5): Accepts either user_id OR group_id (mutually exclusive).
    """

    user_id: UUID | None = Field(
        default=None, description="UUID of the user to grant permission to"
    )
    group_id: UUID | None = Field(
        default=None, description="UUID of the group to grant permission to"
    )
    permission_level: PermissionLevel = Field(
        default=PermissionLevel.READ,
        description="Permission level to grant (READ, WRITE, ADMIN)",
    )

    @model_validator(mode="after")
    def check_mutual_exclusion(self) -> "PermissionCreateExtended":
        """Validate that exactly one of user_id or group_id is provided."""
        if self.user_id and self.group_id:
            raise ValueError("Cannot specify both user_id and group_id")
        if not self.user_id and not self.group_id:
            raise ValueError("Must specify either user_id or group_id")
        return self


class PermissionUpdate(BaseModel):
    """Request schema for updating a permission level.

    Story 5.20 (AC-5.20.3): Edit permission level.
    """

    permission_level: PermissionLevel = Field(
        ..., description="New permission level (READ, WRITE, ADMIN)"
    )


# Response schemas
class PermissionResponse(BaseModel):
    """Response schema for a single permission entry.

    AC1: 201 Created response, AC2: GET list item.
    Includes email joined from users table.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Permission entry UUID")
    user_id: UUID = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    kb_id: UUID = Field(..., description="Knowledge Base UUID")
    permission_level: PermissionLevel = Field(..., description="Permission level")
    created_at: datetime = Field(..., description="When permission was granted")


class PermissionResponseExtended(BaseModel):
    """Extended response schema supporting both user and group permissions.

    Story 5.20 (AC-5.20.5): Returns entity_type to distinguish user/group.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Permission entry UUID")
    entity_type: Literal["user", "group"] = Field(
        ..., description="Type of entity (user or group)"
    )
    entity_id: UUID = Field(..., description="Entity UUID (user_id or group_id)")
    entity_name: str = Field(
        ..., description="Entity name (email for user, name for group)"
    )
    kb_id: UUID = Field(..., description="Knowledge Base UUID")
    permission_level: PermissionLevel = Field(..., description="Permission level")
    created_at: datetime = Field(..., description="When permission was granted")


class PermissionListResponse(BaseModel):
    """Response schema for paginated list of permissions.

    AC2: GET /api/v1/knowledge-bases/{id}/permissions response.
    """

    data: list[PermissionResponse] = Field(
        default_factory=list, description="List of permission entries"
    )
    total: int = Field(..., description="Total number of permissions")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")


class PermissionListResponseExtended(BaseModel):
    """Extended response for paginated list of user and group permissions.

    Story 5.20 (AC-5.20.5): GET /knowledge-bases/{id}/permissions response.
    """

    data: list[PermissionResponseExtended] = Field(
        default_factory=list, description="List of permissions (users and groups)"
    )
    total: int = Field(..., description="Total number of permissions")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")


# Effective permission schemas (Story 5.20 AC-5.20.4)
class PermissionSource(BaseModel):
    """Source information for an effective permission.

    Story 5.20 (AC-5.20.4): Shows where permission comes from (direct vs group).
    """

    type: Literal["direct", "group"] = Field(
        ..., description="Source type (direct user permission or via group)"
    )
    level: PermissionLevel = Field(..., description="Permission level from this source")
    group_id: UUID | None = Field(
        default=None, description="Group ID if source is group"
    )
    group_name: str | None = Field(
        default=None, description="Group name if source is group"
    )


class EffectivePermission(BaseModel):
    """Computed effective permission for a user including group inheritance.

    Story 5.20 (AC-5.20.4): Shows user's effective permission with all sources.
    Direct permission always takes precedence over group permission.
    """

    user_id: UUID = Field(..., description="User UUID")
    user_email: str = Field(..., description="User email address")
    effective_level: PermissionLevel = Field(
        ..., description="Computed effective permission level"
    )
    sources: list[PermissionSource] = Field(
        default_factory=list, description="All permission sources for this user"
    )


class EffectivePermissionListResponse(BaseModel):
    """Response schema for effective permissions endpoint.

    Story 5.20 (AC-5.20.4): GET /knowledge-bases/{id}/effective-permissions.
    """

    data: list[EffectivePermission] = Field(
        default_factory=list, description="List of effective permissions for all users"
    )
    total: int = Field(..., description="Total number of users with permissions")
