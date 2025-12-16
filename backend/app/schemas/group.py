"""Group Pydantic schemas for API request/response validation.

Story 5.19: Group Management (AC-5.19.1)
Story 7.11: Navigation Restructure with RBAC Default Groups
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroupBase(BaseModel):
    """Base schema for group data."""

    name: str = Field(..., min_length=1, max_length=255, description="Group name")
    description: str | None = Field(
        None, max_length=2000, description="Group description"
    )


class GroupCreate(GroupBase):
    """Schema for creating a new group."""

    pass


class GroupUpdate(BaseModel):
    """Schema for updating group data.

    All fields are optional to allow partial updates.
    """

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Group name"
    )
    description: str | None = Field(
        None, max_length=2000, description="Group description"
    )
    is_active: bool | None = Field(None, description="Whether the group is active")


class GroupMemberRead(BaseModel):
    """Schema for group member information."""

    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="Whether the user is active")
    joined_at: datetime = Field(..., description="When the user joined the group")

    model_config = ConfigDict(from_attributes=True)


class GroupRead(BaseModel):
    """Schema for reading group data."""

    id: UUID = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    description: str | None = Field(None, description="Group description")
    is_active: bool = Field(..., description="Whether the group is active")
    permission_level: int = Field(
        ...,
        ge=1,
        le=3,
        description="Permission tier: 1=User, 2=Operator, 3=Administrator",
    )
    is_system: bool = Field(
        ..., description="Whether this is a system group (cannot be deleted)"
    )
    member_count: int = Field(..., description="Number of members in the group")
    created_at: datetime = Field(..., description="When the group was created")
    updated_at: datetime = Field(..., description="When the group was last updated")

    model_config = ConfigDict(from_attributes=True)


class GroupWithMembers(GroupRead):
    """Schema for reading group data with member list."""

    members: list[GroupMemberRead] = Field(
        default_factory=list, description="List of group members"
    )


class GroupMemberAdd(BaseModel):
    """Schema for adding members to a group."""

    user_ids: list[UUID] = Field(
        ..., min_length=1, description="List of user IDs to add"
    )


class GroupMemberAddResponse(BaseModel):
    """Response after adding members to a group."""

    added_count: int = Field(..., description="Number of members successfully added")


class PaginatedGroupResponse(BaseModel):
    """Paginated group list response."""

    items: list[GroupRead] = Field(..., description="List of groups")
    total: int = Field(..., description="Total number of groups matching filters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Engineering Team",
                        "description": "Software engineering team members",
                        "is_active": True,
                        "member_count": 15,
                        "created_at": "2025-12-01T10:00:00Z",
                        "updated_at": "2025-12-05T14:30:00Z",
                    }
                ],
                "total": 25,
                "page": 1,
                "page_size": 20,
                "total_pages": 2,
            }
        }
    )
