"""Document upload API endpoints."""

import io
import math
from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as http_status

from app.core.auth import current_active_user, get_current_operator
from app.core.database import get_async_session
from app.core.redis import get_redis_client
from app.models.document import Document
from app.models.permission import PermissionLevel
from app.models.user import User
from app.schemas.document import (
    ArchiveResponse,
    BulkPurgeRequest,
    BulkPurgeResponse,
    CancelResponse,
    ClearResponse,
    DocumentChunksResponse,
    DocumentContentResponse,
    DocumentDetailResponse,
    DocumentStatus,
    DocumentStatusResponse,
    DocumentUploadResponse,
    DuplicateCheckResponse,
    MarkdownContentResponse,
    PaginatedDocumentResponse,
    PurgeResponse,
    ReplaceResponse,
    RestoreResponse,
    RetryResponse,
    SortField,
    SortOrder,
    UploadErrorResponse,
)
from app.services.chunk_service import ChunkService, ChunkServiceError
from app.services.document_service import DocumentService, DocumentValidationError
from app.services.kb_service import KBService
from app.workers.parsed_content_storage import load_parsed_content

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["documents"])


@router.get(
    "/knowledge-bases/{kb_id}/documents",
    response_model=PaginatedDocumentResponse,
    responses={
        404: {"description": "Knowledge Base not found or no permission"},
    },
)
async def list_documents(
    kb_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Documents per page (max 100)"
    ),
    sort_by: SortField = Query(
        default=SortField.CREATED_AT, description="Field to sort by"
    ),
    sort_order: SortOrder = Query(default=SortOrder.DESC, description="Sort direction"),
    search: str | None = Query(
        default=None, max_length=200, description="Search in document name and filename"
    ),
    status: DocumentStatus | None = Query(
        default=None, description="Filter by document status"
    ),
    mime_type: str | None = Query(default=None, description="Filter by MIME type"),
    tags: list[str] | None = Query(
        default=None, description="Filter by tags (documents must have all specified)"
    ),
    date_from: datetime | None = Query(
        default=None, description="Filter documents created on or after this date"
    ),
    date_to: datetime | None = Query(
        default=None, description="Filter documents created on or before this date"
    ),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedDocumentResponse:
    """List documents in a Knowledge Base with pagination, sorting, and filtering.

    Returns a paginated list of documents with summary information including
    uploader email and status. Documents are sorted by the specified field.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Query Parameters:**
    - page: Page number (default 1)
    - limit: Documents per page (default 20, max 100)
    - sort_by: Sort field (name, created_at, file_size_bytes, status)
    - sort_order: Sort direction (asc, desc)
    - search: Search string to filter by name or filename
    - status: Filter by document status (PENDING, PROCESSING, READY, FAILED, ARCHIVED)
    - mime_type: Filter by MIME type
    - tags: Filter by tags (documents must have all specified tags)
    - date_from: Filter documents created on or after this date
    - date_to: Filter documents created on or before this date

    **Response:**
    - data: Array of document summaries
    - total: Total document count
    - page: Current page number
    - limit: Page size
    - total_pages: Total number of pages
    """
    doc_service = DocumentService(session)

    try:
        documents, total = await doc_service.list_documents(
            kb_id=kb_id,
            user=current_user,
            page=page,
            limit=limit,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
            search=search,
            status=status.value if status else None,
            mime_type=mime_type,
            tags=tags,
            date_from=date_from,
            date_to=date_to,
        )

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedDocumentResponse(
            data=documents,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    except DocumentValidationError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        ) from None


@router.get(
    "/knowledge-bases/{kb_id}/documents/check-duplicate",
    response_model=DuplicateCheckResponse,
    responses={
        404: {"description": "Knowledge Base not found or no permission"},
    },
)
async def check_duplicate(
    kb_id: UUID,
    filename: str = Query(..., description="Filename to check for duplicates"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DuplicateCheckResponse:
    """Check if a document with the same filename already exists.

    Returns information about existing document if found, used by frontend
    to prompt user before upload.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Response:**
    - exists: Whether a duplicate filename exists
    - document_id: ID of existing document (if exists)
    - uploaded_at: When existing document was uploaded (if exists)
    - file_size: Size of existing document in bytes (if exists)
    """
    doc_service = DocumentService(session)

    try:
        result = await doc_service.check_duplicate(kb_id, filename, current_user)
        return DuplicateCheckResponse(**result)

    except DocumentValidationError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Knowledge Base not found",
        ) from None


@router.get(
    "/knowledge-bases/{kb_id}/documents/{doc_id}",
    response_model=DocumentDetailResponse,
    responses={
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def get_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentDetailResponse:
    """Get full document metadata.

    Returns complete document details including all metadata fields,
    processing information, and uploader email.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Response fields:**
    - All document metadata fields
    - uploader_email: Email of the user who uploaded the document
    - processing_started_at, processing_completed_at: Processing timestamps
    - last_error: Error message if document processing failed
    - retry_count: Number of processing retry attempts
    - content: Full document text (if available)
    - metadata: Document metadata from parsing
    """
    doc_service = DocumentService(session)

    try:
        document = await doc_service.get_document(kb_id, doc_id, current_user)

        # Load parsed content if available
        parsed = await load_parsed_content(kb_id, doc_id)
        if parsed:
            document["content"] = parsed.text
            document["metadata"] = parsed.metadata

        return DocumentDetailResponse(**document)

    except DocumentValidationError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=http_status.HTTP_202_ACCEPTED,
    responses={
        400: {
            "model": UploadErrorResponse,
            "description": "Validation error (unsupported type or empty file)",
        },
        404: {
            "description": "Knowledge Base not found or no permission",
        },
        413: {
            "model": UploadErrorResponse,
            "description": "File too large (max 50MB)",
        },
    },
)
async def upload_document(
    kb_id: UUID,
    file: UploadFile = File(..., description="Document file to upload"),
    tags: list[str] | None = Query(
        default=None,
        description="Optional tags for the document (max 10, each max 50 chars)",
    ),
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentUploadResponse:
    """Upload a document to a Knowledge Base.

    **Supported formats:** PDF, DOCX, Markdown (.md)

    **Maximum file size:** 50MB

    The document will be:
    1. Validated for type and size
    2. Uploaded to object storage
    3. Queued for processing (chunking and embedding)

    **Response:** 202 Accepted with document ID and initial metadata.
    The document status will be PENDING until processing completes.

    **Permissions:** Requires WRITE permission on the Knowledge Base.

    **Optional tags:** You can provide tags during upload (max 10 tags, each max 50 chars).

    **Error responses:**
    - 400: Unsupported file type or empty file
    - 404: KB not found or no permission (security through obscurity)
    - 413: File exceeds 50MB limit
    """
    doc_service = DocumentService(session)

    try:
        document, auto_cleared_id = await doc_service.upload(
            kb_id, file, current_user, tags=tags
        )

        # Build response with optional auto-clear message
        message = None
        if auto_cleared_id:
            message = "Previous failed upload was automatically cleared"

        return DocumentUploadResponse(
            id=document.id,
            name=document.name,
            original_filename=document.original_filename,
            mime_type=document.mime_type,
            file_size_bytes=document.file_size_bytes,
            status=document.status,
            tags=document.tags or [],
            created_at=document.created_at,
            auto_cleared_document_id=auto_cleared_id,
            message=message,
        )

    except DocumentValidationError as e:
        logger.warning(
            "document_upload_validation_failed",
            kb_id=str(kb_id),
            error_code=e.code,
            error_message=e.message,
            user_id=str(current_user.id),
        )

        if e.status_code == 404:
            # Don't leak error details for 404
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found",
            ) from None

        if e.status_code == 413:
            raise HTTPException(
                status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details,
                    }
                },
            ) from None

        # 400 and other errors
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.get(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/status",
    response_model=DocumentStatusResponse,
    responses={
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def get_document_status(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentStatusResponse:
    """Get the processing status of a document.

    Returns current status and processing metadata for polling.
    Use this endpoint to check document status during processing.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Response fields:**
    - status: PENDING, PROCESSING, READY, or FAILED
    - chunk_count: Number of chunks (populated when READY)
    - processing_started_at: When processing began
    - processing_completed_at: When processing finished
    - last_error: Error message if FAILED
    - retry_count: Number of retry attempts
    """
    doc_service = DocumentService(session)

    try:
        document = await doc_service.get_status(kb_id, doc_id, current_user)

        return DocumentStatusResponse(
            status=document.status,
            chunk_count=document.chunk_count,
            processing_started_at=document.processing_started_at,
            processing_completed_at=document.processing_completed_at,
            last_error=document.last_error,
            retry_count=document.retry_count,
        )

    except DocumentValidationError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        ) from None


@router.delete(
    "/knowledge-bases/{kb_id}/documents/{doc_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses={
        400: {"description": "Document is in PROCESSING status or already deleted"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def delete_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete a document from a Knowledge Base (soft delete).

    Marks the document as ARCHIVED and queues cleanup of vectors and files.
    The document will no longer appear in listings or search results.

    **Permissions:** Requires WRITE permission on the Knowledge Base.

    **Error responses:**
    - 400: Document is in PROCESSING status (cannot delete) or already deleted
    - 404: Document or KB not found (also returned for no permission - security)
    """
    doc_service = DocumentService(session)

    try:
        await doc_service.delete(kb_id, doc_id, current_user)

    except DocumentValidationError as e:
        logger.warning(
            "document_delete_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error_code=e.code,
            error_message=e.message,
            user_id=str(current_user.id),
        )

        if e.status_code == 404:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        # 400 Bad Request for PROCESSING or already deleted
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.get(
    "/documents/{doc_id}/content",
    response_class=PlainTextResponse,
    responses={
        404: {"description": "Document not found or no permission"},
        400: {"description": "Invalid character range"},
    },
)
async def get_document_content_range(
    doc_id: UUID,
    start: int = Query(..., ge=0, description="Starting character position"),
    end: int = Query(..., ge=0, description="Ending character position"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> str:
    """Get a specific character range from a document for citation preview.

    Returns plain text content from start to end position.
    Used by frontend to display citation context in preview modal.

    **Permissions:** User must have READ access to the document's KB.

    **Security:** Returns 404 (not 403) for unauthorized access.

    Args:
        doc_id: Document UUID
        start: Starting character position (0-indexed)
        end: Ending character position (exclusive)

    Returns:
        Plain text content slice from start to end position.
    """
    kb_service = KBService(session)

    try:
        # Get document to check permissions
        result = await session.execute(
            select(Document.kb_id).where(Document.id == doc_id)
        )
        row = result.one_or_none()

        if not row:
            # Document not found
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        kb_id = row[0]

        # Check user has READ permission on document's KB
        has_permission = await kb_service.check_permission(
            kb_id, current_user, PermissionLevel.READ
        )

        if not has_permission:
            # Security: Return 404 instead of 403 to not leak document existence
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Load parsed content from MinIO
        parsed = await load_parsed_content(kb_id, doc_id)

        if not parsed or not parsed.text:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document content not available",
            )

        content = parsed.text

        # Validate range
        if start > len(content) or end > len(content) or start < 0 or end < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid character range",
            )

        if start > end:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Start position must be less than or equal to end position",
            )

        # Return content slice
        return content[start:end]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_document_content_range_failed",
            doc_id=str(doc_id),
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document content",
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/retry",
    response_model=RetryResponse,
    status_code=http_status.HTTP_202_ACCEPTED,
    responses={
        400: {"description": "Document is not in FAILED status"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def retry_document_processing(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> RetryResponse:
    """Retry processing a failed document.

    Resets the document status to PENDING and queues it for reprocessing.
    Only documents in FAILED status can be retried.

    **Permissions:** Requires WRITE permission on the Knowledge Base.

    **Response:** 202 Accepted on success.

    **Error responses:**
    - 400: Document is not in FAILED status
    - 404: Document or KB not found (security through obscurity)
    """
    doc_service = DocumentService(session)

    try:
        await doc_service.retry(kb_id, doc_id, current_user)

        return RetryResponse(message="Document processing retry initiated")

    except DocumentValidationError as e:
        logger.warning(
            "document_retry_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error_code=e.code,
            error_message=e.message,
            user_id=str(current_user.id),
        )

        if e.status_code == 404:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        # 400 Bad Request for invalid status
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/cancel",
    response_model=CancelResponse,
    status_code=http_status.HTTP_200_OK,
    responses={
        400: {"description": "Document is not in PROCESSING or PENDING status"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def cancel_document_processing(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> CancelResponse:
    """Cancel processing of a document.

    Marks a PROCESSING or PENDING document as FAILED so it can be
    retried later or deleted.

    **Permissions:** Requires WRITE permission on the Knowledge Base.

    **Response:** 200 OK on success.

    **Error responses:**
    - 400: Document is not in PROCESSING or PENDING status
    - 404: Document or KB not found (security through obscurity)
    """
    doc_service = DocumentService(session)

    try:
        await doc_service.cancel(kb_id, doc_id, current_user)

        return CancelResponse(message="Document processing cancelled")

    except DocumentValidationError as e:
        logger.warning(
            "document_cancel_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error_code=e.code,
            error_message=e.message,
            user_id=str(current_user.id),
        )

        if e.status_code == 404:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        # 400 Bad Request for invalid status
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/reupload",
    response_model=DocumentUploadResponse,
    status_code=http_status.HTTP_202_ACCEPTED,
    responses={
        400: {
            "model": UploadErrorResponse,
            "description": "Validation error (MIME type mismatch or empty file)",
        },
        404: {
            "description": "Document or Knowledge Base not found or no permission",
        },
        413: {
            "model": UploadErrorResponse,
            "description": "File too large (max 50MB)",
        },
    },
)
async def reupload_document(
    kb_id: UUID,
    doc_id: UUID,
    file: UploadFile = File(..., description="Replacement document file"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentUploadResponse:
    """Re-upload a document to replace existing content.

    Replaces the document file while preserving the document ID and metadata.
    The new file must have the same MIME type as the original.

    **Process:**
    1. Current version metadata archived to version_history
    2. New file uploaded (overwrites in storage)
    3. Document queued for reprocessing
    4. Old vectors remain searchable until new processing completes

    **Permissions:** Requires WRITE permission on the Knowledge Base.

    **Error responses:**
    - 400: MIME type mismatch or empty file
    - 404: Document/KB not found or no permission
    - 413: File exceeds 50MB limit
    """
    doc_service = DocumentService(session)

    try:
        document = await doc_service.replace_document(kb_id, doc_id, file, current_user)

        return DocumentUploadResponse(
            id=document.id,
            name=document.name,
            original_filename=document.original_filename,
            mime_type=document.mime_type,
            file_size_bytes=document.file_size_bytes,
            status=document.status,
            created_at=document.created_at,
        )

    except DocumentValidationError as e:
        logger.warning(
            "document_reupload_validation_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error_code=e.code,
            error_message=e.message,
            user_id=str(current_user.id),
        )

        if e.status_code == 404:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        if e.status_code == 413:
            raise HTTPException(
                status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details,
                    }
                },
            ) from None

        # 400 and other errors
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
    response_model=ArchiveResponse,
    status_code=http_status.HTTP_200_OK,
    responses={
        400: {"description": "Document is not in READY status or already archived"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def archive_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> ArchiveResponse:
    """Archive a completed document (soft-delete without removing data).

    This endpoint marks a document as archived, which:
    - Sets the archived_at timestamp
    - Updates Qdrant payload to exclude from search results
    - Logs an audit event

    Only documents with READY status can be archived.
    Archived documents remain in storage but are excluded from searches.

    Args:
        kb_id: Knowledge base UUID
        doc_id: Document UUID
        current_user: Authenticated user (requires WRITE permission)
        session: Database session

    Returns:
        ArchiveResponse with success message and timestamp

    Raises:
        404: Document or KB not found
        400: Document is not READY or already archived
    """
    document_service = DocumentService(session)

    try:
        document = await document_service.archive(
            kb_id=kb_id,
            doc_id=doc_id,
            user=current_user,
        )
        return ArchiveResponse(
            message="Document archived successfully",
            archived_at=document.archived_at,
        )
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
    response_model=RestoreResponse,
    status_code=http_status.HTTP_200_OK,
    responses={
        400: {"description": "Document is not archived"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def restore_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> RestoreResponse:
    """Restore an archived document (Story 6-2).

    This endpoint restores an archived document, which:
    - Clears the archived_at timestamp
    - Updates Qdrant payload to include in search results again
    - Logs an audit event

    Only archived documents can be restored.

    Args:
        kb_id: Knowledge base UUID
        doc_id: Document UUID
        current_user: Authenticated user (requires WRITE permission)
        session: Database session

    Returns:
        RestoreResponse with success message and timestamp

    Raises:
        404: Document or KB not found
        400: Document is not archived
    """
    document_service = DocumentService(session)

    try:
        document = await document_service.restore(
            kb_id=kb_id,
            doc_id=doc_id,
            user=current_user,
        )
        return RestoreResponse(
            message="Document restored successfully",
            restored_at=document.updated_at,
        )
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.delete(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
    response_model=PurgeResponse,
    status_code=http_status.HTTP_200_OK,
    responses={
        400: {"description": "Document is not archived (must archive first)"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def purge_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> PurgeResponse:
    """Permanently delete an archived document (Story 6-3).

    This endpoint permanently deletes an archived document:
    - Deletes vectors from Qdrant
    - Deletes file from MinIO
    - Hard deletes database record
    - Logs an audit event

    Only archived documents can be purged. This action is irreversible.

    Args:
        kb_id: Knowledge base UUID
        doc_id: Document UUID
        current_user: Authenticated user (requires ADMIN permission or KB owner)
        session: Database session

    Returns:
        PurgeResponse with success message

    Raises:
        404: Document or KB not found
        400: Document is not archived
    """
    document_service = DocumentService(session)

    try:
        await document_service.purge_document(
            kb_id=kb_id,
            doc_id=doc_id,
            user=current_user,
        )
        return PurgeResponse(message="Document permanently deleted")
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/bulk-purge",
    response_model=BulkPurgeResponse,
    status_code=http_status.HTTP_200_OK,
    responses={
        404: {"description": "Knowledge Base not found"},
    },
)
async def bulk_purge_documents(
    kb_id: UUID,
    request: BulkPurgeRequest,
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> BulkPurgeResponse:
    """Permanently delete multiple archived documents (Story 6-3).

    This endpoint permanently deletes multiple archived documents at once.
    Non-archived documents in the list will be skipped.

    Args:
        kb_id: Knowledge base UUID
        request: BulkPurgeRequest containing list of document IDs
        current_user: Authenticated user (requires ADMIN permission or KB owner)
        session: Database session

    Returns:
        BulkPurgeResponse with purged count and skipped IDs

    Raises:
        404: KB not found
    """
    document_service = DocumentService(session)

    try:
        result = await document_service.bulk_purge(
            kb_id=kb_id,
            document_ids=request.document_ids,
            user=current_user,
        )
        return BulkPurgeResponse(
            message=f"Purged {result['purged']} documents",
            purged=result["purged"],
            skipped=result["skipped"],
            skipped_ids=result["skipped_ids"],
        )
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.delete(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
    response_model=ClearResponse,
    status_code=http_status.HTTP_200_OK,
    responses={
        400: {"description": "Document is not in FAILED status"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def clear_failed_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> ClearResponse:
    """Clear a failed document from the system (Story 6-4).

    This endpoint removes a failed document:
    - Deletes any partial vectors from Qdrant
    - Deletes uploaded file from MinIO
    - Hard deletes database record
    - Logs an audit event

    Only documents with FAILED status can be cleared.

    Args:
        kb_id: Knowledge base UUID
        doc_id: Document UUID
        current_user: Authenticated user (requires WRITE permission)
        session: Database session

    Returns:
        ClearResponse with success message

    Raises:
        404: Document or KB not found
        400: Document is not in FAILED status
    """
    document_service = DocumentService(session)

    try:
        await document_service.clear_failed_document(
            kb_id=kb_id,
            doc_id=doc_id,
            user=current_user,
        )
        return ClearResponse(message="Failed document cleared successfully")
    except DocumentValidationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
    response_model=ReplaceResponse,
    status_code=http_status.HTTP_200_OK,
    responses={
        400: {
            "description": "Document is in PROCESSING status or validation error",
        },
        404: {"description": "Document or Knowledge Base not found"},
        413: {"description": "File too large (max 50MB)"},
    },
)
async def replace_document(
    kb_id: UUID,
    doc_id: UUID,
    file: UploadFile = File(..., description="New document file"),
    current_user: User = Depends(get_current_operator),
    session: AsyncSession = Depends(get_async_session),
) -> ReplaceResponse:
    """Replace an existing document with a new file (Story 6-6).

    This endpoint performs an atomic replace operation:
    - Deletes old vectors from Qdrant
    - Deletes old file from MinIO
    - Uploads new file to MinIO
    - Updates document metadata (preserves ID, created_at, tags)
    - Sets status to PENDING for reprocessing
    - Queues new Celery task
    - Logs an audit event

    Cannot replace while document is in PROCESSING status.

    Args:
        kb_id: Knowledge base UUID
        doc_id: Document UUID
        file: New document file (multipart/form-data)
        current_user: Authenticated user (requires WRITE permission)
        session: Database session

    Returns:
        ReplaceResponse with updated document details

    Raises:
        404: Document or KB not found
        400: Document is in PROCESSING status
        413: File exceeds 50MB limit
    """
    document_service = DocumentService(session)

    try:
        document = await document_service.replace_document(
            kb_id=kb_id,
            doc_id=doc_id,
            file=file,
            user=current_user,
        )
        return ReplaceResponse(
            id=document.id,
            name=document.name,
            status=document.status,
            message="Document replaced and queued for processing",
        )
    except DocumentValidationError as e:
        logger.warning(
            "document_replace_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error_code=e.code,
            error_message=e.message,
            user_id=str(current_user.id),
        )

        if e.status_code == 404:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        if e.status_code == 413:
            raise HTTPException(
                status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details,
                    }
                },
            ) from None

        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            },
        ) from None


# Story 5-25: Document Chunk Viewer Backend


@router.get(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/chunks",
    response_model=DocumentChunksResponse,
    responses={
        404: {"description": "Document or Knowledge Base not found"},
        500: {"description": "Failed to retrieve chunks from Qdrant"},
    },
)
async def get_document_chunks(
    kb_id: UUID,
    doc_id: UUID,
    cursor: int = Query(
        default=0, ge=0, description="Starting chunk_index for pagination"
    ),
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum chunks to return (max 100)"
    ),
    search: str | None = Query(
        default=None,
        max_length=500,
        description="Optional search query to filter and rank chunks by relevance",
    ),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    redis_client: Redis = Depends(get_redis_client),
) -> DocumentChunksResponse:
    """Get paginated chunks for a document (Story 5-25).

    Returns document chunks from Qdrant with cursor-based pagination.
    Optionally filter and rank chunks by semantic search query.

    **AC-5.25.1:** Returns chunk_id, chunk_index, text, char_start, char_end,
                   page_number, section_header for each chunk.

    **AC-5.25.2:** Cursor-based pagination using chunk_index.

    **AC-5.25.3:** Search with query embedding and relevance score.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Query Parameters:**
    - cursor: Starting chunk_index (0-indexed, default 0)
    - limit: Max chunks per page (default 50, max 100)
    - search: Optional search query for semantic filtering

    **Response:**
    - chunks: Array of chunk objects
    - total: Total chunk count for document
    - has_more: Whether more chunks exist
    - next_cursor: Next chunk_index for pagination (null if no more)
    """
    kb_service = KBService(session)

    try:
        # First verify KB exists and user has permission
        has_permission = await kb_service.check_permission(
            kb_id, current_user, PermissionLevel.READ
        )

        if not has_permission:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found",
            )

        # Verify document exists in this KB
        result = await session.execute(
            select(Document.id).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Get chunks from Qdrant
        # Story 7-17: Pass session and redis for KB-aware embedding model resolution
        chunk_service = ChunkService(kb_id, session=session, redis=redis_client)
        chunks_response = await chunk_service.get_chunks(
            document_id=doc_id,
            cursor=cursor,
            limit=limit,
            search_query=search,
        )

        return chunks_response

    except HTTPException:
        raise
    except ChunkServiceError as e:
        logger.error(
            "get_document_chunks_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error=e.message,
            error_code=e.code,
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document chunks",
        ) from None
    except Exception as e:
        logger.error(
            "get_document_chunks_unexpected_error",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document chunks",
        ) from None


@router.get(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/full-content",
    response_model=DocumentContentResponse,
    responses={
        404: {"description": "Document or Knowledge Base not found"},
        400: {"description": "Document content not available"},
    },
)
async def get_document_full_content(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentContentResponse:
    """Get full document content with optional HTML rendering (Story 5-25).

    Returns the complete document text content along with MIME type.
    For DOCX documents, also returns an HTML rendering using mammoth.

    **AC-5.25.4:** Returns text, mime_type, and html (for DOCX only).

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Response:**
    - text: Full document text content
    - mime_type: Document MIME type (e.g., "application/pdf")
    - html: HTML rendering for DOCX documents (null for other types)
    """
    kb_service = KBService(session)

    try:
        # Verify KB permission
        has_permission = await kb_service.check_permission(
            kb_id, current_user, PermissionLevel.READ
        )

        if not has_permission:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found",
            )

        # Get document to verify it exists and get mime_type
        result = await session.execute(
            select(Document.id, Document.mime_type, Document.file_path).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
            )
        )
        row = result.one_or_none()

        if not row:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        _doc_id, mime_type, file_path = row

        # Try to load parsed content from storage first
        parsed = await load_parsed_content(kb_id, doc_id)
        text_content = parsed.text if parsed else None

        # If parsed content not available, try to reconstruct from chunks
        if not text_content:
            chunk_service = ChunkService(kb_id)
            try:
                chunks_response = await chunk_service.get_chunks(
                    document_id=doc_id,
                    cursor=0,
                    limit=10000,  # Get all chunks
                )
                if chunks_response and chunks_response.chunks:
                    # Concatenate chunk text to reconstruct document text
                    text_content = "\n\n".join(
                        chunk.text for chunk in chunks_response.chunks if chunk.text
                    )
                    logger.info(
                        "document_content_reconstructed_from_chunks",
                        kb_id=str(kb_id),
                        doc_id=str(doc_id),
                        chunk_count=len(chunks_response.chunks),
                    )
            except ChunkServiceError:
                pass  # Chunks not available, continue

        # For DOCX files, generate HTML using mammoth (works even if text_content is empty)
        html_content = None
        if (
            mime_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            html_content = await _convert_docx_to_html(kb_id, doc_id, file_path)
            # If we have HTML but no text, try to extract text from chunks as fallback
            if html_content and not text_content:
                # Use HTML content as fallback text (stripped of tags for basic viewing)
                import re

                text_content = (
                    re.sub(r"<[^>]+>", "", html_content) if html_content else None
                )

        # If still no content available, return error
        if not text_content and not html_content:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Document content not available",
            )

        return DocumentContentResponse(
            text=text_content or "",
            mime_type=mime_type,
            html=html_content,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_document_full_content_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document content",
        ) from None


async def _convert_docx_to_html(
    kb_id: UUID, doc_id: UUID, file_path: str | None
) -> str | None:
    """Convert DOCX document to HTML using mammoth.

    Downloads the DOCX file from MinIO and converts it to HTML.

    Args:
        kb_id: Knowledge base UUID
        doc_id: Document UUID
        file_path: Path to file in MinIO

    Returns:
        HTML string or None if conversion fails
    """
    if not file_path:
        return None

    try:
        import io

        import mammoth

        from app.integrations.minio_client import minio_service

        # Extract object path from file_path (format: kb-{uuid}/{object_path})
        # file_path is stored as "kb-{kb_id}/{doc_id}/{filename}"
        path_parts = file_path.split("/", 1)
        if len(path_parts) != 2:
            logger.warning(
                "docx_invalid_file_path",
                kb_id=str(kb_id),
                doc_id=str(doc_id),
                file_path=file_path,
            )
            return None
        object_path = path_parts[1]

        # Download DOCX file from MinIO
        file_bytes = await minio_service.download_file(kb_id, object_path)

        if not file_bytes:
            logger.warning(
                "docx_download_failed",
                kb_id=str(kb_id),
                doc_id=str(doc_id),
                file_path=file_path,
            )
            return None

        # Convert to HTML using mammoth
        file_stream = io.BytesIO(file_bytes)
        result = mammoth.convert_to_html(file_stream)

        if result.messages:
            for msg in result.messages:
                logger.debug(
                    "mammoth_conversion_message",
                    doc_id=str(doc_id),
                    message=str(msg),
                )

        return result.value

    except Exception as e:
        logger.error(
            "docx_to_html_conversion_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error=str(e),
        )
        return None


@router.get(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/download",
    responses={
        404: {"description": "Document or Knowledge Base not found"},
        400: {"description": "Document file not available"},
    },
)
async def download_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """Download the original document file (Story 5-26).

    Returns the original document file for rendering in viewers (e.g., PDF.js).
    Supports PDF, DOCX, and other file types.

    **AC-5.26.4:** Enables content pane to render documents based on type.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Response:**
    - StreamingResponse with appropriate Content-Type and Content-Disposition headers
    """
    from app.integrations.minio_client import minio_service

    kb_service = KBService(session)

    try:
        # Verify KB permission
        has_permission = await kb_service.check_permission(
            kb_id, current_user, PermissionLevel.READ
        )

        if not has_permission:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found",
            )

        # Get document to verify it exists and get file info
        result = await session.execute(
            select(
                Document.id,
                Document.file_path,
                Document.mime_type,
                Document.original_filename,
            ).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
            )
        )
        row = result.one_or_none()

        if not row:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        _doc_id, file_path, mime_type, original_filename = row

        if not file_path:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Document file not available",
            )

        # Extract object path from file_path (format: kb-{uuid}/{object_path})
        # file_path is stored as "kb-{kb_id}/{doc_id}/{filename}"
        path_parts = file_path.split("/", 1)
        if len(path_parts) != 2:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path format",
            )
        object_path = path_parts[1]

        # Download file from MinIO
        file_bytes = await minio_service.download_file(kb_id, object_path)

        if not file_bytes:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Document file not available",
            )

        # Create streaming response
        file_stream = io.BytesIO(file_bytes)

        # Determine content type
        content_type = mime_type or "application/octet-stream"

        # Set filename for Content-Disposition
        filename = original_filename or f"document_{doc_id}"

        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Length": str(len(file_bytes)),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "download_document_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document",
        ) from None


@router.get(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
    response_model=MarkdownContentResponse,
    responses={
        400: {"description": "Document is still processing"},
        403: {"description": "Forbidden - no read access"},
        404: {"description": "Document or markdown not found"},
    },
)
async def get_markdown_content(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> MarkdownContentResponse:
    """Get markdown content for a document (Story 7-29).

    Used by chunk viewer for precise character-based highlighting.
    Returns the generated markdown content from document parsing.

    **AC-7.29.1:** Returns markdown_content and generated_at for valid documents.
    **AC-7.29.2:** Returns 404 if markdown content not available (older documents).
    **AC-7.29.3:** Returns 400 if document is still processing.
    **AC-7.29.5:** Returns 403 if user lacks read permission on KB.

    **Permissions:** Requires READ permission on the Knowledge Base.
    """
    kb_service = KBService(session)

    try:
        # AC-7.29.5: Verify KB permission
        has_permission = await kb_service.check_permission(
            kb_id, current_user, PermissionLevel.READ
        )

        if not has_permission:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="No read access to this Knowledge Base",
            )

        # Get document to verify it exists and check status
        result = await session.execute(
            select(
                Document.id,
                Document.status,
                Document.processing_completed_at,
            ).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
            )
        )
        row = result.one_or_none()

        if not row:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        _doc_id, doc_status, processing_completed_at = row

        # AC-7.29.3: Check if document is still processing
        if doc_status in ("PENDING", "PROCESSING"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Document is still processing",
            )

        # Load parsed content from MinIO
        parsed_content = await load_parsed_content(kb_id, doc_id)

        # AC-7.29.2: Check markdown availability
        if not parsed_content or not parsed_content.markdown_content:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Markdown content not available for this document",
            )

        # AC-7.29.4: Return response with markdown content
        # Use processing_completed_at as the generation timestamp
        generated_at = processing_completed_at

        # Fallback to current time if no timestamp available
        if not generated_at:
            from datetime import UTC

            generated_at = datetime.now(UTC)

        return MarkdownContentResponse(
            document_id=doc_id,
            markdown_content=parsed_content.markdown_content,
            generated_at=generated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_markdown_content_failed",
            kb_id=str(kb_id),
            doc_id=str(doc_id),
            error=str(e),
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve markdown content",
        ) from None
