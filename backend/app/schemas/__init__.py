"""Pydantic schemas for API request/response validation."""

from app.schemas.citation import Citation, CitationMappingError
from app.schemas.document import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    DocumentErrorCode,
    DocumentListItem,
    DocumentResponse,
    DocumentStatus,
    DocumentUploadResponse,
    DocumentValidationError,
)
from app.schemas.search import (
    ExplainRequest,
    ExplanationResponse,
    QuickSearchRequest,
    QuickSearchResponse,
    QuickSearchResult,
    RelatedDocument,
    SearchRequest,
    SearchResponse,
    SearchResultSchema,
    SimilarSearchRequest,
)
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    # User
    "UserCreate",
    "UserRead",
    "UserUpdate",
    # Document
    "DocumentStatus",
    "DocumentUploadResponse",
    "DocumentResponse",
    "DocumentListItem",
    "DocumentValidationError",
    "DocumentErrorCode",
    "ALLOWED_MIME_TYPES",
    "ALLOWED_EXTENSIONS",
    "MAX_FILE_SIZE_BYTES",
    "MAX_FILE_SIZE_MB",
    # Search
    "SearchRequest",
    "SearchResponse",
    "SearchResultSchema",
    "QuickSearchRequest",
    "QuickSearchResponse",
    "QuickSearchResult",
    "SimilarSearchRequest",
    "ExplainRequest",
    "ExplanationResponse",
    "RelatedDocument",
    # Citation
    "Citation",
    "CitationMappingError",
]
