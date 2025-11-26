"""Permission Pydantic schemas for Knowledge Base access control."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
