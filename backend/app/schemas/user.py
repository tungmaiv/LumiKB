"""User Pydantic schemas for API request/response validation.

Story 7.11: Added permission_level to UserRead.
"""

from datetime import datetime
from uuid import UUID

from fastapi_users import schemas
from pydantic import Field


class UserRead(schemas.BaseUser[UUID]):
    """Schema for reading user data.

    Inherits from FastAPI-Users BaseUser:
    - id: UUID
    - email: EmailStr
    - is_active: bool
    - is_superuser: bool
    - is_verified: bool

    Additional fields:
    - created_at: datetime
    - onboarding_completed: bool
    - last_active: datetime | None
    - permission_level: int (1=User, 2=Operator, 3=Administrator)
    """

    created_at: datetime
    onboarding_completed: bool
    last_active: datetime | None
    permission_level: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Permission tier: 1=User, 2=Operator, 3=Administrator",
    )


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user.

    Inherits from FastAPI-Users BaseUserCreate:
    - email: EmailStr
    - password: str
    - is_active: bool = True
    - is_superuser: bool = False
    - is_verified: bool = False
    """

    password: str = Field(..., min_length=8)


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data.

    Inherits from FastAPI-Users BaseUserUpdate:
    - password: str | None = None
    - email: EmailStr | None = None
    - is_active: bool | None = None
    - is_superuser: bool | None = None
    - is_verified: bool | None = None
    """

    pass


class AdminUserUpdate(schemas.BaseModel):
    """Schema for admin user updates (activation/deactivation).

    Used by admin endpoints to update user status.
    """

    is_active: bool | None = None
