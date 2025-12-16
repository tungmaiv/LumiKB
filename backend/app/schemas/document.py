"""Document Pydantic schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Constants for validation
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MAX_FILE_SIZE_MB = 50

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/markdown": ".md",
    "text/x-markdown": ".md",  # Alternative markdown MIME
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md"}

# Tag validation constants
MAX_TAGS_PER_DOCUMENT = 10
MAX_TAG_LENGTH = 50


class DocumentStatus(str, Enum):
    """Document processing status for API responses."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


def validate_tags(tags: list[str]) -> list[str]:
    """Validate and normalize tags.

    - Converts to lowercase
    - Strips whitespace
    - Truncates to max length
    - Removes empty tags
    - Limits to max tags

    Args:
        tags: List of raw tag strings.

    Returns:
        List of validated and normalized tags.
    """
    validated = []
    for tag in tags:
        if not tag:
            continue
        # Strip, lowercase, and truncate
        normalized = tag.strip().lower()[:MAX_TAG_LENGTH]
        if normalized and normalized not in validated:
            validated.append(normalized)
        if len(validated) >= MAX_TAGS_PER_DOCUMENT:
            break
    return validated


class DocumentTagsUpdate(BaseModel):
    """Schema for updating document tags."""

    tags: list[str] = Field(
        default=[],
        max_length=MAX_TAGS_PER_DOCUMENT,
        description="List of tags (max 10, each max 50 chars)",
    )

    @field_validator("tags")
    @classmethod
    def validate_tag_list(cls, v: list[str]) -> list[str]:
        """Validate and normalize tags."""
        return validate_tags(v)


class DocumentUploadResponse(BaseModel):
    """Response schema after successful document upload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    tags: list[str] = Field(default=[])
    created_at: datetime
    # Story 6-5: Auto-cleared document info
    auto_cleared_document_id: UUID | None = Field(
        default=None,
        description="ID of auto-cleared failed document if duplicate was replaced",
    )
    message: str | None = Field(
        default=None,
        description="Additional message about upload (e.g., auto-clear notification)",
    )


class DocumentResponse(BaseModel):
    """Full document details response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kb_id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_path: str | None
    checksum: str
    status: DocumentStatus
    chunk_count: int
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    last_error: str | None
    retry_count: int
    uploaded_by: UUID | None
    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    """Document summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentValidationError(BaseModel):
    """Error response for document validation failures."""

    code: str
    message: str
    details: dict | None = None


class UploadErrorResponse(BaseModel):
    """Standardized upload error response."""

    error: DocumentValidationError


class DocumentStatusResponse(BaseModel):
    """Response schema for document status endpoint.

    Returns current processing status and metadata.
    Used for polling during document processing.

    Fields:
    - status: Current processing status (PENDING, PROCESSING, READY, FAILED)
    - chunk_count: Number of chunks after processing (0 if not ready)
    - processing_started_at: When processing began (null if PENDING)
    - processing_completed_at: When processing finished (null if not complete)
    - last_error: Error message if FAILED (null otherwise)
    - retry_count: Number of retry attempts
    """

    model_config = ConfigDict(from_attributes=True)

    status: DocumentStatus
    chunk_count: int
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    last_error: str | None
    retry_count: int


class RetryResponse(BaseModel):
    """Response schema for document retry endpoint."""

    message: str


class CancelResponse(BaseModel):
    """Response schema for document cancel endpoint."""

    message: str


class ArchiveResponse(BaseModel):
    """Response schema for document archive endpoint."""

    message: str
    archived_at: datetime


class RestoreResponse(BaseModel):
    """Response schema for document restore endpoint (Story 6-2)."""

    message: str
    restored_at: datetime


class PurgeResponse(BaseModel):
    """Response schema for document purge endpoint (Story 6-3)."""

    message: str


class BulkPurgeResponse(BaseModel):
    """Response schema for bulk purge endpoint (Story 6-3)."""

    message: str
    purged: int
    skipped: int
    skipped_ids: list[str] = Field(default=[])


class BulkPurgeRequest(BaseModel):
    """Request schema for bulk purge endpoint (Story 6-3)."""

    document_ids: list[UUID] = Field(
        ...,
        description="List of document IDs to purge (max 100 per request)",
        min_length=1,
        max_length=100,  # Rate limiting: max batch size
    )


class ClearResponse(BaseModel):
    """Response schema for clear failed document endpoint (Story 6-4)."""

    message: str


class ReplaceResponse(BaseModel):
    """Response schema for replace document endpoint (Story 6-6)."""

    id: UUID
    name: str
    status: DocumentStatus
    message: str


# Error codes for document validation
class DocumentErrorCode(str, Enum):
    """Error codes for document validation."""

    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    EMPTY_FILE = "EMPTY_FILE"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    MIME_TYPE_MISMATCH = "MIME_TYPE_MISMATCH"


class DocumentListItemWithUploader(BaseModel):
    """Document summary for list views with uploader info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    uploaded_by: UUID | None
    uploader_email: str | None = None
    version_number: int = 1
    tags: list[str] = Field(default=[])


class PaginatedDocumentResponse(BaseModel):
    """Paginated response for document list endpoint."""

    data: list[DocumentListItemWithUploader]
    total: int
    page: int
    limit: int
    total_pages: int


class ArchivedDocumentItem(BaseModel):
    """Schema for archived document list item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    chunk_count: int
    archived_at: datetime
    created_at: datetime
    tags: list[str] = Field(default=[])
    uploader_email: str | None = None


class PaginatedArchivedDocumentsResponse(BaseModel):
    """Paginated response for archived documents list endpoint."""

    data: list[ArchivedDocumentItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class DocumentDetailResponse(BaseModel):
    """Full document details response with uploader info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kb_id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_path: str | None
    checksum: str
    status: DocumentStatus
    chunk_count: int
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    last_error: str | None
    retry_count: int
    uploaded_by: UUID | None
    uploader_email: str | None = None
    version_number: int = 1
    version_history: list[dict] | None = None
    tags: list[str] = Field(default=[])
    created_at: datetime
    updated_at: datetime
    content: str | None = None
    metadata: dict | None = None


class SortField(str, Enum):
    """Allowed sort fields for document list."""

    NAME = "name"
    CREATED_AT = "created_at"
    FILE_SIZE_BYTES = "file_size_bytes"
    STATUS = "status"


class SortOrder(str, Enum):
    """Sort order for document list."""

    ASC = "asc"
    DESC = "desc"


class VersionHistoryEntry(BaseModel):
    """Schema for a single version history entry.

    Tracks metadata from previous document versions before replacement.
    """

    version_number: int
    file_size: int
    checksum: str
    replaced_at: datetime
    replaced_by: UUID


class DuplicateCheckResponse(BaseModel):
    """Response schema for duplicate filename check endpoint."""

    exists: bool
    document_id: UUID | None = None
    uploaded_at: datetime | None = None
    file_size: int | None = None


# Processing Step Tracking Schemas (Story 5-23)


class ProcessingStep(str, Enum):
    """Document processing pipeline steps."""

    UPLOAD = "upload"
    PARSE = "parse"
    CHUNK = "chunk"
    EMBED = "embed"
    INDEX = "index"
    COMPLETE = "complete"


class StepStatus(str, Enum):
    """Status of individual processing steps."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


class ProcessingStepInfo(BaseModel):
    """Information about a single processing step."""

    step: ProcessingStep
    status: StepStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error: str | None = None


class DocumentProcessingStatus(BaseModel):
    """Document summary with processing status for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    file_type: str  # Derived from mime_type (e.g., "PDF", "DOCX")
    file_size: int  # Alias for file_size_bytes
    status: DocumentStatus
    current_step: ProcessingStep
    chunk_count: int | None = None
    created_at: datetime
    updated_at: datetime


class DocumentProcessingDetails(BaseModel):
    """Detailed processing status for a single document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    file_type: str  # Derived from mime_type
    file_size: int  # Alias for file_size_bytes
    status: DocumentStatus
    current_step: ProcessingStep
    chunk_count: int | None = None
    total_duration_ms: int | None = None
    steps: list[ProcessingStepInfo]
    created_at: datetime
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None


class PaginatedDocumentProcessingResponse(BaseModel):
    """Paginated response for document processing list endpoint."""

    documents: list[DocumentProcessingStatus]
    total: int
    page: int
    page_size: int


class ProcessingFilters(BaseModel):
    """Filters for document processing list query."""

    name: str | None = None
    file_type: str | None = None
    status: DocumentStatus | None = None
    current_step: ProcessingStep | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "created_at"
    sort_order: str = "desc"


class DocumentFilters(BaseModel):
    """Filters for document list query (Story 5-24)."""

    search: str | None = Field(
        default=None,
        description="Search in document name and filename",
        max_length=200,
    )
    status: DocumentStatus | None = Field(
        default=None,
        description="Filter by document status",
    )
    mime_type: str | None = Field(
        default=None,
        description="Filter by MIME type",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Filter by tags (documents must have all specified tags)",
        max_length=MAX_TAGS_PER_DOCUMENT,
    )
    date_from: datetime | None = Field(
        default=None,
        description="Filter documents created on or after this date",
    )
    date_to: datetime | None = Field(
        default=None,
        description="Filter documents created on or before this date",
    )


# Story 5-25: Document Chunk Viewer Backend Schemas


class DocumentChunkResponse(BaseModel):
    """Schema for a single document chunk from Qdrant.

    AC-5.25.1: chunk_id, chunk_index, text, char_start, char_end, page_number, section_header
    """

    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(..., description="Qdrant point ID (UUID)")
    chunk_index: int = Field(..., description="Position in document (0-indexed)")
    text: str = Field(..., description="Chunk text content")
    char_start: int = Field(..., description="Start character offset in document")
    char_end: int = Field(..., description="End character offset in document")
    page_number: int | None = Field(None, description="Page number if PDF")
    section_header: str | None = Field(None, description="Section header if available")
    score: float | None = Field(
        None, description="Search relevance score (if search query)"
    )


class DocumentChunksResponse(BaseModel):
    """Paginated response for document chunks endpoint.

    AC-5.25.2: Cursor-based pagination with has_more indicator.
    """

    chunks: list[DocumentChunkResponse] = Field(
        default=[], description="List of chunks"
    )
    total: int = Field(..., description="Total number of chunks for this document")
    has_more: bool = Field(..., description="Whether more chunks exist after cursor")
    next_cursor: int | None = Field(None, description="Next chunk_index for pagination")


class DocumentContentResponse(BaseModel):
    """Response for document content endpoint.

    AC-5.25.4: Returns full text, mime_type, and optional HTML for DOCX.
    """

    text: str = Field(..., description="Full document text content")
    mime_type: str = Field(..., description="Document MIME type")
    html: str | None = Field(None, description="HTML rendering for DOCX documents")


class MarkdownContentResponse(BaseModel):
    """Response schema for document markdown content endpoint.

    Story 7-29: Returns generated markdown for chunk viewer highlighting.
    Used by frontend to render document content with precise character-based
    highlighting using char_start and char_end positions.
    """

    document_id: UUID = Field(..., description="Document UUID")
    markdown_content: str = Field(
        ..., description="Full document content in Markdown format"
    )
    generated_at: datetime = Field(
        ..., description="When markdown was generated during parsing"
    )
