"""Knowledge Base statistics schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopDocument(BaseModel):
    """Top accessed document within a Knowledge Base."""

    id: UUID = Field(..., description="Document UUID")
    filename: str = Field(..., description="Document filename")
    access_count: int = Field(..., description="Number of accesses in period")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc-123-def-456",
                "filename": "quarterly-report-2024.pdf",
                "access_count": 42,
            }
        }
    )


class KBDetailedStats(BaseModel):
    """Detailed Knowledge Base statistics for admin view.

    Aggregates metrics from PostgreSQL, MinIO, and Qdrant.
    Refreshed on-demand with 10-minute Redis caching.
    """

    kb_id: UUID = Field(..., description="Knowledge Base UUID")
    kb_name: str = Field(..., description="Knowledge Base name")

    # Document metrics (PostgreSQL)
    document_count: int = Field(..., description="Total documents in KB")

    # Storage metrics (MinIO)
    storage_bytes: int = Field(..., description="Total storage used in bytes")

    # Vector metrics (Qdrant)
    total_chunks: int = Field(..., description="Total chunks (points) in Qdrant")
    total_embeddings: int = Field(
        ..., description="Total embeddings (vectors) in Qdrant"
    )

    # Usage metrics (audit.events)
    searches_30d: int = Field(..., description="Search count in last 30 days")
    generations_30d: int = Field(..., description="Generation count in last 30 days")
    unique_users_30d: int = Field(..., description="Unique users in last 30 days")

    # Top documents (audit.events)
    top_documents: list[TopDocument] = Field(
        ..., description="Top 5 most accessed documents"
    )

    # Metadata
    last_updated: datetime = Field(..., description="Last stats refresh timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "kb_id": "abc-123-def-456",
                "kb_name": "Engineering Documentation",
                "document_count": 42,
                "storage_bytes": 104857600,  # 100MB
                "total_chunks": 1250,
                "total_embeddings": 1250,
                "searches_30d": 285,
                "generations_30d": 98,
                "unique_users_30d": 12,
                "top_documents": [
                    {
                        "id": "doc-123",
                        "filename": "api-reference.pdf",
                        "access_count": 42,
                    },
                    {
                        "id": "doc-456",
                        "filename": "architecture-guide.md",
                        "access_count": 38,
                    },
                    {
                        "id": "doc-789",
                        "filename": "deployment-runbook.pdf",
                        "access_count": 35,
                    },
                ],
                "last_updated": "2025-12-03T10:15:00Z",
            }
        }
    )
