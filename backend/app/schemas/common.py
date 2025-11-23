"""Common Pydantic schemas for API responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    data: list[T]
    meta: PaginationMeta
