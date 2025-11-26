"""Document upload API endpoints."""

import math
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.models.document import Document
from app.models.permission import PermissionLevel
from app.models.user import User
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    DuplicateCheckResponse,
    PaginatedDocumentResponse,
    RetryResponse,
    SortField,
    SortOrder,
    UploadErrorResponse,
)
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
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedDocumentResponse:
    """List documents in a Knowledge Base with pagination and sorting.

    Returns a paginated list of documents with summary information including
    uploader email and status. Documents are sorted by the specified field.

    **Permissions:** Requires READ permission on the Knowledge Base.

    **Query Parameters:**
    - page: Page number (default 1)
    - limit: Documents per page (default 20, max 100)
    - sort_by: Sort field (name, created_at, file_size_bytes, status)
    - sort_order: Sort direction (asc, desc)

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
            status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
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
    current_user: User = Depends(current_active_user),
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

    **Error responses:**
    - 400: Unsupported file type or empty file
    - 404: KB not found or no permission (security through obscurity)
    - 413: File exceeds 50MB limit
    """
    doc_service = DocumentService(session)

    try:
        document = await doc_service.upload(kb_id, file, current_user)

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
            "document_upload_validation_failed",
            kb_id=str(kb_id),
            error_code=e.code,
            error_message=e.message,
            user_id=str(current_user.id),
        )

        if e.status_code == 404:
            # Don't leak error details for 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge Base not found",
            ) from None

        if e.status_code == 413:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        ) from None


@router.delete(
    "/knowledge-bases/{kb_id}/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"description": "Document is in PROCESSING status or already deleted"},
        404: {"description": "Document or Knowledge Base not found"},
    },
)
async def delete_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(current_active_user),
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        # 400 Bad Request for PROCESSING or already deleted
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
                status_code=status.HTTP_404_NOT_FOUND,
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Load parsed content from MinIO
        parsed = await load_parsed_content(kb_id, doc_id)

        if not parsed or not parsed.text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document content not available",
            )

        content = parsed.text

        # Validate range
        if start > len(content) or end > len(content) or start < 0 or end < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid character range",
            )

        if start > end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document content",
        ) from None


@router.post(
    "/knowledge-bases/{kb_id}/documents/{doc_id}/retry",
    response_model=RetryResponse,
    status_code=status.HTTP_202_ACCEPTED,
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        # 400 Bad Request for invalid status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
    status_code=status.HTTP_202_ACCEPTED,
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            ) from None

        if e.status_code == 413:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
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
