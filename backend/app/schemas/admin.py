"""Admin dashboard schemas."""

from pydantic import BaseModel, ConfigDict, Field


class UserStats(BaseModel):
    """User statistics."""

    total: int = Field(..., description="Total registered users")
    active: int = Field(..., description="Users active in last 30 days")
    inactive: int = Field(..., description="Inactive users")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 150,
                "active": 120,
                "inactive": 30,
            }
        }
    )


class KnowledgeBaseStats(BaseModel):
    """Knowledge Base statistics."""

    total: int = Field(..., description="Total knowledge bases")
    by_status: dict[str, int] = Field(
        ..., description="Knowledge base counts by status"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 45,
                "by_status": {"active": 40, "archived": 5},
            }
        }
    )


class DocumentStats(BaseModel):
    """Document statistics."""

    total: int = Field(..., description="Total documents")
    by_status: dict[str, int] = Field(..., description="Document counts by status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1250,
                "by_status": {"READY": 1100, "PENDING": 50, "FAILED": 100},
            }
        }
    )


class StorageStats(BaseModel):
    """Storage usage statistics."""

    total_bytes: int = Field(..., description="Total storage used in bytes")
    avg_doc_size_bytes: int = Field(
        ..., description="Average document size in bytes"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_bytes": 524288000,  # ~500MB
                "avg_doc_size_bytes": 419430,  # ~410KB
            }
        }
    )


class PeriodStats(BaseModel):
    """Activity statistics for time periods."""

    last_24h: int = Field(..., description="Count in last 24 hours")
    last_7d: int = Field(..., description="Count in last 7 days")
    last_30d: int = Field(..., description="Count in last 30 days")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "last_24h": 42,
                "last_7d": 285,
                "last_30d": 1150,
            }
        }
    )


class ActivityStats(BaseModel):
    """User activity statistics."""

    searches: PeriodStats = Field(..., description="Search query counts")
    generations: PeriodStats = Field(..., description="Generation request counts")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "searches": {
                    "last_24h": 42,
                    "last_7d": 285,
                    "last_30d": 1150,
                },
                "generations": {
                    "last_24h": 15,
                    "last_7d": 98,
                    "last_30d": 420,
                },
            }
        }
    )


class TrendData(BaseModel):
    """Trend data for sparkline visualization."""

    searches: list[int] = Field(
        ..., description="Daily search counts for last 30 days"
    )
    generations: list[int] = Field(
        ..., description="Daily generation counts for last 30 days"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "searches": [38, 42, 35, 40, 45, 50, 48, 52, 55, 60] + [0] * 20,
                "generations": [12, 15, 18, 20, 22, 25, 28, 30, 32, 35] + [0] * 20,
            }
        }
    )


class AdminStats(BaseModel):
    """Comprehensive admin dashboard statistics.

    Aggregates system-wide metrics for monitoring and capacity planning.
    Results cached in Redis for 5 minutes to reduce database load.
    """

    users: UserStats = Field(..., description="User statistics")
    knowledge_bases: KnowledgeBaseStats = Field(
        ..., description="Knowledge base statistics"
    )
    documents: DocumentStats = Field(..., description="Document statistics")
    storage: StorageStats = Field(..., description="Storage usage statistics")
    activity: ActivityStats = Field(..., description="User activity statistics")
    trends: TrendData = Field(
        ..., description="Trend data for sparkline visualization (last 30 days)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": {"total": 150, "active": 120, "inactive": 30},
                "knowledge_bases": {
                    "total": 45,
                    "by_status": {"active": 40, "archived": 5},
                },
                "documents": {
                    "total": 1250,
                    "by_status": {"READY": 1100, "PENDING": 50, "FAILED": 100},
                },
                "storage": {
                    "total_bytes": 524288000,
                    "avg_doc_size_bytes": 419430,
                },
                "activity": {
                    "searches": {
                        "last_24h": 42,
                        "last_7d": 285,
                        "last_30d": 1150,
                    },
                    "generations": {
                        "last_24h": 15,
                        "last_7d": 98,
                        "last_30d": 420,
                    },
                },
                "trends": {
                    "searches": [38, 42, 35, 40, 45, 50, 48, 52, 55, 60] + [0] * 20,
                    "generations": [12, 15, 18, 20, 22, 25, 28, 30, 32, 35]
                    + [0] * 20,
                },
            }
        }
    )
