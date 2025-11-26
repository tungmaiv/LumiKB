"""Document Pydantic schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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


class DocumentStatus(str, Enum):
    """Document processing status for API responses."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class DocumentUploadResponse(BaseModel):
    """Response schema after successful document upload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    created_at: datetime


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


class PaginatedDocumentResponse(BaseModel):
    """Paginated response for document list endpoint."""

    data: list[DocumentListItemWithUploader]
    total: int
    page: int
    limit: int
    total_pages: int


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
