"""Document service for upload and management business logic."""

import contextlib
import os
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import UUID

import structlog
from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.minio_client import compute_checksum, minio_service
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.outbox import Outbox
from app.models.permission import PermissionLevel
from app.models.user import User
from app.schemas.document import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    DocumentProcessingDetails,
    DocumentProcessingStatus,
    ProcessingFilters,
    ProcessingStepInfo,
    validate_tags,
)
from app.schemas.document import (
    ProcessingStep as ProcessingStepSchema,
)
from app.schemas.document import (
    StepStatus as StepStatusSchema,
)
from app.services.audit_service import audit_service
from app.services.kb_service import KBService

logger = structlog.get_logger(__name__)


class DocumentValidationError(Exception):
    """Raised when document validation fails."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class DocumentService:
    """Service for document operations.

    Handles business logic for document upload, validation,
    and coordination with MinIO storage and outbox events.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize DocumentService with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session
        self._kb_service: KBService | None = None

    @property
    def kb_service(self) -> KBService:
        """Lazy initialization of KBService."""
        if self._kb_service is None:
            self._kb_service = KBService(self.session)
        return self._kb_service

    async def upload(
        self,
        kb_id: UUID,
        file: UploadFile,
        user: User,
        tags: list[str] | None = None,
    ) -> tuple[Document, UUID | None]:
        """Upload a document to a Knowledge Base.

        Validates the upload, stores in MinIO, creates document record,
        and queues for processing.

        Args:
            kb_id: The Knowledge Base UUID.
            file: The uploaded file.
            user: The user uploading the document.
            tags: Optional list of tags for the document.

        Returns:
            Tuple of (Document, auto_cleared_document_id or None).

        Raises:
            DocumentValidationError: If validation fails.
        """
        # 1. Check KB exists and user has WRITE permission
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            # AC6, AC7: Return 404 to not leak KB existence
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Knowledge Base not found",
                status_code=404,
            )

        # 2. Read file content for validation
        content = await file.read()
        file_size = len(content)

        # 3. Validate file
        await self._validate_file(file, file_size)

        # 4. Compute checksum
        file_stream = BytesIO(content)
        checksum = compute_checksum(file_stream)
        file_stream.seek(0)

        # 5. Story 6-5: Case-insensitive duplicate detection with auto-clear
        # AC-6.5.1: Case-insensitive match on filename
        existing_result = await self.session.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                func.lower(Document.original_filename)
                == func.lower(file.filename or "untitled"),
                Document.deleted_at.is_(None),
            )
        )
        existing_doc = existing_result.scalar_one_or_none()
        auto_cleared_id = None

        if existing_doc:
            # AC-6.5.3: Auto-clear failed duplicates
            if existing_doc.status == DocumentStatus.FAILED:
                logger.info(
                    "auto_clearing_failed_duplicate",
                    kb_id=str(kb_id),
                    existing_doc_id=str(existing_doc.id),
                    filename=file.filename,
                )
                auto_cleared_id = existing_doc.id
                await self.clear_failed_document(
                    kb_id=kb_id,
                    doc_id=existing_doc.id,
                    user=user,
                    reason="duplicate_upload",
                )
            # AC-6.5.4: Block pending/processing duplicates
            elif existing_doc.status in (
                DocumentStatus.PENDING,
                DocumentStatus.PROCESSING,
            ):
                raise DocumentValidationError(
                    code="DUPLICATE_PROCESSING",
                    message="A document with this name is currently being processed",
                    status_code=409,
                    details={
                        "error": "duplicate_document",
                        "existing_document_id": str(existing_doc.id),
                        "existing_status": existing_doc.status.value,
                    },
                )
            # AC-6.5.2: 409 for completed/archived duplicates
            else:
                raise DocumentValidationError(
                    code="DUPLICATE_DOCUMENT",
                    message="A document with this name already exists",
                    status_code=409,
                    details={
                        "error": "duplicate_document",
                        "existing_document_id": str(existing_doc.id),
                        "existing_status": existing_doc.status.value
                        if existing_doc.archived_at is None
                        else "archived",
                    },
                )

        # 7. Upload to MinIO FIRST before creating document record
        # Tech Debt Fix P1: Reordered operations - MinIO upload before DB record
        # This ensures failed uploads don't leave orphan DB records
        from uuid import uuid4

        temp_doc_id = uuid4()
        object_path = f"{temp_doc_id}/{file.filename}"
        try:
            full_path = await minio_service.upload_file(
                kb_id=kb_id,
                object_path=object_path,
                file=file_stream,
                content_type=file.content_type or "application/octet-stream",
            )
        except Exception as e:
            logger.error(
                "document_upload_minio_failed",
                kb_id=str(kb_id),
                error=str(e),
            )
            raise DocumentValidationError(
                code="UPLOAD_FAILED",
                message="Failed to upload file to storage",
                status_code=500,
                details={"error": str(e)},
            ) from e

        # 8. Generate document record with the pre-assigned ID
        # Validate tags if provided
        validated_tags = validate_tags(tags) if tags else []

        document = Document(
            id=temp_doc_id,
            kb_id=kb_id,
            name=self._generate_document_name(file.filename or "untitled"),
            original_filename=file.filename or "untitled",
            mime_type=file.content_type or "application/octet-stream",
            file_size_bytes=file_size,
            checksum=checksum,
            status=DocumentStatus.PENDING,
            uploaded_by=user.id,
            file_path=full_path,
            tags=validated_tags,
        )
        self.session.add(document)
        await self.session.flush()  # Ensure document is persisted

        # 9. Create outbox event for processing (same transaction)
        outbox_event = Outbox(
            event_type="document.process",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": full_path,
                "mime_type": file.content_type,
                "checksum": checksum,
            },
        )
        self.session.add(outbox_event)

        # 10. Audit log (async, fire-and-forget)
        await audit_service.log_event(
            action="document.uploaded",
            resource_type="document",
            user_id=user.id,
            resource_id=document.id,
            details={
                "kb_id": str(kb_id),
                "filename": file.filename,
                "mime_type": file.content_type,
                "file_size_bytes": file_size,
                "tags": validated_tags,
            },
        )

        logger.info(
            "document_uploaded",
            document_id=str(document.id),
            kb_id=str(kb_id),
            filename=file.filename,
            file_size=file_size,
            user_id=str(user.id),
            auto_cleared_id=str(auto_cleared_id) if auto_cleared_id else None,
        )

        return document, auto_cleared_id

    async def _check_kb_permission(self, kb_id: UUID, user: User) -> bool:
        """Check if KB exists and user has WRITE permission.

        Args:
            kb_id: The Knowledge Base UUID.
            user: The user to check.

        Returns:
            True if KB exists and user has WRITE permission.
        """
        # Check KB exists
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return False

        # Check WRITE permission
        return await self.kb_service.check_permission(
            kb_id, user, PermissionLevel.WRITE
        )

    async def _validate_file(
        self,
        file: UploadFile,
        file_size: int,
    ) -> None:
        """Validate file type and size.

        Args:
            file: The uploaded file.
            file_size: Size in bytes.

        Raises:
            DocumentValidationError: If validation fails.
        """
        # AC5: Check empty file
        if file_size == 0:
            raise DocumentValidationError(
                code="EMPTY_FILE",
                message="Empty file not allowed",
                status_code=400,
            )

        # AC4: Check file size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise DocumentValidationError(
                code="FILE_TOO_LARGE",
                message=f"File exceeds {MAX_FILE_SIZE_MB}MB limit",
                status_code=413,
                details={
                    "size_bytes": file_size,
                    "max_bytes": MAX_FILE_SIZE_BYTES,
                },
            )

        # AC3: Check MIME type
        content_type = file.content_type or ""
        filename = file.filename or ""
        extension = os.path.splitext(filename)[1].lower() if filename else ""

        # Validate by MIME type or extension
        is_valid_mime = content_type in ALLOWED_MIME_TYPES
        is_valid_ext = extension in ALLOWED_EXTENSIONS

        if not is_valid_mime and not is_valid_ext:
            raise DocumentValidationError(
                code="UNSUPPORTED_FILE_TYPE",
                message="File type not allowed",
                status_code=400,
                details={
                    "mime_type": content_type,
                    "extension": extension,
                    "allowed_mime_types": list(ALLOWED_MIME_TYPES.keys()),
                    "allowed_extensions": list(ALLOWED_EXTENSIONS),
                },
            )

    def _generate_document_name(self, filename: str) -> str:
        """Generate a display name from filename.

        Removes extension and cleans up the name.

        Args:
            filename: Original filename.

        Returns:
            Clean display name.
        """
        name = os.path.splitext(filename)[0]
        # Replace underscores and hyphens with spaces
        name = name.replace("_", " ").replace("-", " ")
        # Capitalize words
        return " ".join(word.capitalize() for word in name.split())

    async def get_status(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> Document:
        """Get document status for polling.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting status.

        Returns:
            The Document record with status fields.

        Raises:
            DocumentValidationError: If document not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        return document

    async def retry(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> Document:
        """Retry processing a failed document.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting retry.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is not in FAILED status.
        """
        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Check document is in FAILED status
        if document.status != DocumentStatus.FAILED:
            raise DocumentValidationError(
                code="INVALID_STATUS",
                message="Only FAILED documents can be retried",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # Reset document for retry
        document.status = DocumentStatus.PENDING
        document.retry_count = 0
        document.last_error = None
        document.processing_started_at = None
        document.processing_completed_at = None

        # Create outbox event for processing
        outbox_event = Outbox(
            event_type="document.process",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": document.file_path,
                "mime_type": document.mime_type,
                "checksum": document.checksum,
                "is_retry": True,
            },
        )
        self.session.add(outbox_event)

        # Audit log
        await audit_service.log_event(
            action="document.retry",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "previous_error": document.last_error,
            },
        )

        logger.info(
            "document_retry_initiated",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

        return document

    async def cancel(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> Document:
        """Cancel processing of a document.

        Marks a PROCESSING or PENDING document as FAILED so it can be
        retried later or deleted.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting cancellation.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is not in PROCESSING/PENDING status.
        """
        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Check document is in PROCESSING or PENDING status
        if document.status not in (DocumentStatus.PROCESSING, DocumentStatus.PENDING):
            raise DocumentValidationError(
                code="INVALID_STATUS",
                message="Only PROCESSING or PENDING documents can be cancelled",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # Mark document as FAILED with cancellation message
        document.status = DocumentStatus.FAILED
        document.last_error = "Processing cancelled by user"
        document.processing_completed_at = datetime.now(UTC)

        # Audit log
        await audit_service.log_event(
            action="document.cancel",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "previous_status": document.status.value,
            },
        )

        logger.info(
            "document_processing_cancelled",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

        return document

    async def _check_kb_read_permission(self, kb_id: UUID, user: User) -> bool:
        """Check if KB exists and user has READ permission.

        Args:
            kb_id: The Knowledge Base UUID.
            user: The user to check.

        Returns:
            True if KB exists and user has READ permission.
        """
        # Check KB exists
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.status == "active",
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            return False

        # Check READ permission
        return await self.kb_service.check_permission(kb_id, user, PermissionLevel.READ)

    async def list_documents(
        self,
        kb_id: UUID,
        user: User,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: str | None = None,
        status: str | None = None,
        mime_type: str | None = None,
        tags: list[str] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[dict], int]:
        """List documents in a Knowledge Base with pagination, sorting, and filtering.

        Args:
            kb_id: The Knowledge Base UUID.
            user: The user requesting the list.
            page: Page number (1-indexed).
            limit: Documents per page (max 100).
            sort_by: Field to sort by (name, created_at, file_size_bytes, status).
            sort_order: Sort direction (asc, desc).
            search: Search string to filter by name or filename.
            status: Filter by document status.
            mime_type: Filter by MIME type.
            tags: Filter by tags (documents must have all specified tags).
            date_from: Filter documents created on or after this date.
            date_to: Filter documents created on or before this date.

        Returns:
            Tuple of (list of document dicts with uploader info, total count).

        Raises:
            DocumentValidationError: If KB not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Knowledge Base not found",
                status_code=404,
            )

        # Validate and clamp limit
        limit = min(max(1, limit), 100)
        page = max(1, page)
        offset = (page - 1) * limit

        # Build filter conditions
        # Exclude deleted and archived documents from main list
        filter_conditions = [
            Document.kb_id == kb_id,
            Document.deleted_at.is_(None),
            Document.archived_at.is_(None),
        ]

        # Apply search filter (name or original_filename)
        if search:
            search_pattern = f"%{search.lower()}%"
            filter_conditions.append(
                or_(
                    func.lower(Document.name).like(search_pattern),
                    func.lower(Document.original_filename).like(search_pattern),
                )
            )

        # Apply status filter
        if status:
            filter_conditions.append(Document.status == status)

        # Apply MIME type filter
        if mime_type:
            filter_conditions.append(Document.mime_type == mime_type)

        # Apply tags filter (documents must have ALL specified tags)
        if tags:
            for tag in tags:
                # Use PostgreSQL's @> operator for JSONB contains
                filter_conditions.append(Document.tags.contains([tag.lower().strip()]))

        # Apply date range filters
        if date_from:
            filter_conditions.append(Document.created_at >= date_from)
        if date_to:
            filter_conditions.append(Document.created_at <= date_to)

        # Build base query with all filters
        base_query = select(Document).where(*filter_conditions)

        # Get total count with filters applied
        count_query = select(func.count(Document.id)).where(*filter_conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Document, sort_by, Document.created_at)
        sort_column = sort_column.desc() if sort_order == "desc" else sort_column.asc()

        # Apply pagination and execute
        query = base_query.order_by(sort_column).offset(offset).limit(limit)
        result = await self.session.execute(query)
        documents = result.scalars().all()

        # Build result with uploader info
        document_list = []
        for doc in documents:
            # Fetch uploader email if uploaded_by is set
            uploader_email = None
            if doc.uploaded_by:
                uploader_result = await self.session.execute(
                    select(User.email).where(User.id == doc.uploaded_by)
                )
                uploader_email = uploader_result.scalar_one_or_none()

            document_list.append(
                {
                    "id": doc.id,
                    "name": doc.name,
                    "original_filename": doc.original_filename,
                    "mime_type": doc.mime_type,
                    "file_size_bytes": doc.file_size_bytes,
                    "status": doc.status,
                    "chunk_count": doc.chunk_count,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                    "uploaded_by": doc.uploaded_by,
                    "uploader_email": uploader_email,
                    "tags": doc.tags or [],
                }
            )

        return document_list, total

    async def delete(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> None:
        """Delete (soft) a document from a Knowledge Base.

        Sets document status to ARCHIVED, sets deleted_at timestamp,
        and creates an outbox event for cleanup of vectors and files.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting deletion.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is in PROCESSING status.
        """
        from datetime import datetime

        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Check document is not in PROCESSING status (AC6)
        if document.status == DocumentStatus.PROCESSING:
            raise DocumentValidationError(
                code="PROCESSING_IN_PROGRESS",
                message="Cannot delete while processing. Please wait.",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # Check document is not already ARCHIVED
        if document.status == DocumentStatus.ARCHIVED:
            raise DocumentValidationError(
                code="ALREADY_DELETED",
                message="Document has already been deleted",
                status_code=400,
            )

        # Soft delete: Set status to ARCHIVED and deleted_at timestamp
        document.status = DocumentStatus.ARCHIVED
        document.deleted_at = datetime.now(UTC)

        # Create outbox event for cleanup (AC2, AC3)
        outbox_event = Outbox(
            event_type="document.delete",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": document.file_path,
            },
        )
        self.session.add(outbox_event)

        # Audit log (AC2) - fire-and-forget
        await audit_service.log_event(
            action="document.deleted",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "document_name": document.name,
            },
        )

        logger.info(
            "document_deleted",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

    async def get_document(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> dict:
        """Get full document details with uploader info.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting the document.

        Returns:
            Document dict with all fields and uploader email.

        Raises:
            DocumentValidationError: If document not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Fetch uploader email if uploaded_by is set
        uploader_email = None
        if document.uploaded_by:
            uploader_result = await self.session.execute(
                select(User.email).where(User.id == document.uploaded_by)
            )
            uploader_email = uploader_result.scalar_one_or_none()

        return {
            "id": document.id,
            "kb_id": document.kb_id,
            "name": document.name,
            "original_filename": document.original_filename,
            "mime_type": document.mime_type,
            "file_size_bytes": document.file_size_bytes,
            "file_path": document.file_path,
            "checksum": document.checksum,
            "status": document.status,
            "chunk_count": document.chunk_count,
            "processing_started_at": document.processing_started_at,
            "processing_completed_at": document.processing_completed_at,
            "last_error": document.last_error,
            "retry_count": document.retry_count,
            "uploaded_by": document.uploaded_by,
            "uploader_email": uploader_email,
            "version_number": document.version_number,
            "version_history": document.version_history,
            "tags": document.tags or [],
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }

    async def check_duplicate(
        self,
        kb_id: UUID,
        filename: str,
        user: User,
    ) -> dict:
        """Check if a document with the same filename exists in the KB.

        Args:
            kb_id: The Knowledge Base UUID.
            filename: The filename to check.
            user: The user checking.

        Returns:
            Dict with exists=True/False and document info if found.

        Raises:
            DocumentValidationError: If KB not found or no permission.
        """
        # Check READ permission on KB
        has_permission = await self._check_kb_read_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Knowledge Base not found",
                status_code=404,
            )

        # Search for existing document with same filename
        result = await self.session.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                Document.original_filename == filename,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            return {"exists": False}

        return {
            "exists": True,
            "document_id": document.id,
            "uploaded_at": document.created_at,
            "file_size": document.file_size_bytes,
        }

    async def replace_document(
        self,
        kb_id: UUID,
        doc_id: UUID,
        file: UploadFile,
        user: User,
    ) -> Document:
        """Replace an existing document with a new file version.

        Story 6-6: Performs atomic delete-then-upload of document content.
        Preserves document ID and created_at, updates name to new filename.

        Transaction boundaries:
        - Old Qdrant vectors: Deleted first (safe - regenerated on reprocessing)
        - Old MinIO file: Deleted with graceful failure handling
        - New MinIO file: Must upload successfully, or operation aborts
        - Database: Updated only after successful MinIO upload (transactional)

        If new file upload fails, the document remains in its original state
        in the database, though old vectors/file may have been deleted.
        Reprocessing will regenerate vectors from the original file path.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID to replace.
            file: The new file.
            user: The user replacing the document.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                document is processing, or file validation fails.
        """

        from qdrant_client.http import models as qdrant_models

        from app.integrations.qdrant_client import qdrant_service

        # 1. Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # 2. Get existing document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # AC-6.6.4: Cannot replace while processing
        if document.status == DocumentStatus.PROCESSING:
            raise DocumentValidationError(
                code="PROCESSING_IN_PROGRESS",
                message="Cannot replace document while processing is in progress",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # 3. Read and validate new file
        content = await file.read()
        file_size = len(content)

        # Check empty file
        if file_size == 0:
            raise DocumentValidationError(
                code="EMPTY_FILE",
                message="Empty file not allowed",
                status_code=400,
            )

        # Check file size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise DocumentValidationError(
                code="FILE_TOO_LARGE",
                message=f"File exceeds {MAX_FILE_SIZE_MB}MB limit",
                status_code=413,
                details={
                    "size_bytes": file_size,
                    "max_bytes": MAX_FILE_SIZE_BYTES,
                },
            )

        # 4. Compute new checksum
        file_stream = BytesIO(content)
        new_checksum = compute_checksum(file_stream)
        file_stream.seek(0)

        # AC-6.6.2: Delete old Qdrant vectors first (atomic delete-then-upload)
        try:
            collection_name = f"kb_{kb_id}"
            qdrant_service.client.delete(
                collection_name=collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=str(doc_id)),
                            )
                        ]
                    )
                ),
                wait=True,
            )
            logger.info(
                "qdrant_vectors_deleted_for_replace",
                document_id=str(doc_id),
                kb_id=str(kb_id),
            )
        except Exception as e:
            logger.warning(
                "qdrant_replace_cleanup_failed",
                document_id=str(doc_id),
                kb_id=str(kb_id),
                error=str(e),
            )
            # Continue even if Qdrant cleanup fails

        # AC-6.6.2: Delete old MinIO file
        old_file_path = document.file_path
        if old_file_path:
            try:
                # Extract object_path from full path (bucket/object_path)
                # file_path format: kb-{uuid}/{doc_id}/{filename}
                parts = old_file_path.split("/", 1)
                object_path_to_delete = parts[1] if len(parts) > 1 else old_file_path
                await minio_service.delete_file(kb_id, object_path_to_delete)
                logger.info(
                    "minio_file_deleted_for_replace",
                    document_id=str(doc_id),
                    old_file_path=old_file_path,
                )
            except Exception as e:
                logger.warning(
                    "minio_replace_cleanup_failed",
                    document_id=str(doc_id),
                    old_file_path=old_file_path,
                    error=str(e),
                )
                # Continue even if MinIO cleanup fails

        # 5. Upload new file to MinIO with new filename
        new_filename = file.filename or document.original_filename
        new_content_type = file.content_type or "application/octet-stream"
        object_path = f"{document.id}/{new_filename}"
        try:
            full_path = await minio_service.upload_file(
                kb_id=kb_id,
                object_path=object_path,
                file=file_stream,
                content_type=new_content_type,
            )
        except Exception as e:
            logger.error(
                "document_replace_minio_failed",
                kb_id=str(kb_id),
                document_id=str(doc_id),
                error=str(e),
            )
            raise DocumentValidationError(
                code="UPLOAD_FAILED",
                message="Failed to upload replacement file to storage",
                status_code=500,
                details={"error": str(e)},
            ) from e

        # 6. Update document metadata
        # AC-6.6.3: Preserve ID, created_at, tags; update name to new filename
        old_name = document.name
        old_checksum = document.checksum
        old_size = document.file_size_bytes

        document.name = self._generate_document_name(new_filename)
        document.original_filename = new_filename
        document.mime_type = new_content_type
        document.file_size_bytes = file_size
        document.checksum = new_checksum
        document.file_path = full_path
        document.status = DocumentStatus.PENDING
        document.archived_at = None  # Clear if was archived
        document.last_error = None
        document.processing_started_at = None
        document.processing_completed_at = None
        # Preserve: id, created_at, tags, kb_id

        # 7. Create outbox event for reprocessing
        outbox_event = Outbox(
            event_type="document.process",
            aggregate_id=document.id,
            aggregate_type="document",
            payload={
                "document_id": str(document.id),
                "kb_id": str(kb_id),
                "file_path": full_path,
                "mime_type": new_content_type,
                "checksum": new_checksum,
                "reason": "replacement",
                "is_replacement": True,
            },
        )
        self.session.add(outbox_event)

        # 8. Audit log with action="document_replaced" (AC-6.6.1)
        await audit_service.log_event(
            action="document_replaced",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "old_name": old_name,
                "new_name": document.name,
                "old_checksum": old_checksum,
                "new_checksum": new_checksum,
                "old_size": old_size,
                "new_size": file_size,
            },
        )

        logger.info(
            "document_replaced",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            old_name=old_name,
            new_name=document.name,
            user_id=str(user.id),
        )

        return document

    # Story 5-23: Document Processing Progress Screen

    def _get_file_type(self, mime_type: str) -> str:
        """Convert MIME type to display file type.

        Args:
            mime_type: MIME type string.

        Returns:
            Display file type (e.g., "PDF", "DOCX", "MD").
        """
        mime_to_type = {
            "application/pdf": "PDF",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
            "text/markdown": "MD",
            "text/x-markdown": "MD",
            "text/plain": "TXT",
        }
        return mime_to_type.get(mime_type, mime_type.split("/")[-1].upper())

    async def list_with_processing_status(
        self,
        kb_id: UUID,
        filters: ProcessingFilters,
    ) -> tuple[list[DocumentProcessingStatus], int]:
        """List documents with processing status for progress monitoring.

        Args:
            kb_id: The Knowledge Base UUID.
            filters: Filtering and pagination parameters.

        Returns:
            Tuple of (list of DocumentProcessingStatus, total count).
        """
        from sqlalchemy import and_, or_

        # Build base query - exclude deleted and archived documents
        conditions = [
            Document.kb_id == kb_id,
            Document.deleted_at.is_(None),
            Document.archived_at.is_(None),
        ]

        # Apply filters
        if filters.name:
            conditions.append(Document.original_filename.ilike(f"%{filters.name}%"))

        if filters.file_type:
            # Map file_type to MIME types
            file_type_lower = filters.file_type.lower()
            mime_conditions = []
            if file_type_lower == "pdf":
                mime_conditions.append(Document.mime_type == "application/pdf")
            elif file_type_lower == "docx":
                mime_conditions.append(
                    Document.mime_type
                    == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            elif file_type_lower in ("md", "markdown"):
                mime_conditions.append(
                    or_(
                        Document.mime_type == "text/markdown",
                        Document.mime_type == "text/x-markdown",
                    )
                )
            elif file_type_lower == "txt":
                mime_conditions.append(Document.mime_type == "text/plain")
            if mime_conditions:
                conditions.append(or_(*mime_conditions))

        if filters.status:
            conditions.append(Document.status == filters.status)

        if filters.current_step:
            conditions.append(Document.current_step == filters.current_step.value)

        if filters.date_from:
            conditions.append(Document.created_at >= filters.date_from)

        if filters.date_to:
            conditions.append(Document.created_at <= filters.date_to)

        # Get total count
        count_query = select(func.count(Document.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting
        sort_field_map = {
            "created_at": Document.created_at,
            "original_filename": Document.original_filename,
            "file_size_bytes": Document.file_size_bytes,
            "status": Document.status,
            "current_step": Document.current_step,
            "chunk_count": Document.chunk_count,
        }
        sort_column = sort_field_map.get(filters.sort_by, Document.created_at)
        if filters.sort_order == "asc":
            sort_column = sort_column.asc()
        else:
            sort_column = sort_column.desc()

        # Calculate pagination
        offset = (filters.page - 1) * filters.page_size

        # Execute query
        query = (
            select(Document)
            .where(and_(*conditions))
            .order_by(sort_column)
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.session.execute(query)
        documents = result.scalars().all()

        # Convert to response schema
        processing_list = []
        for doc in documents:
            # Map current_step string to enum, handling existing documents
            try:
                current_step = ProcessingStepSchema(doc.current_step)
            except ValueError:
                # Default to COMPLETE for existing documents without step tracking
                current_step = ProcessingStepSchema.COMPLETE

            processing_list.append(
                DocumentProcessingStatus(
                    id=doc.id,
                    original_filename=doc.original_filename,
                    file_type=self._get_file_type(doc.mime_type),
                    file_size=doc.file_size_bytes,
                    status=doc.status,
                    current_step=current_step,
                    chunk_count=doc.chunk_count if doc.chunk_count > 0 else None,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
            )

        return processing_list, total

    async def get_processing_details(
        self,
        doc_id: UUID,
    ) -> DocumentProcessingDetails | None:
        """Get detailed processing status for a single document.

        Args:
            doc_id: The Document UUID.

        Returns:
            DocumentProcessingDetails or None if not found.
        """
        from datetime import datetime

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            return None

        # Build step info from processing_steps JSONB
        steps: list[ProcessingStepInfo] = []
        total_duration_ms = 0
        processing_steps = document.processing_steps or {}
        step_errors = document.step_errors or {}

        # Define pipeline order (must include 'complete' to match frontend)
        pipeline_order = ["upload", "parse", "chunk", "embed", "index", "complete"]

        for step_name in pipeline_order:
            step_data = processing_steps.get(step_name, {})
            error_data = step_errors.get(step_name, {})

            # Determine step status
            if step_data.get("status"):
                try:
                    status = StepStatusSchema(step_data["status"])
                except ValueError:
                    status = StepStatusSchema.PENDING
            else:
                # Infer status for existing documents without step tracking
                if document.status == DocumentStatus.READY:
                    status = StepStatusSchema.DONE
                elif document.status == DocumentStatus.FAILED:
                    # Mark all steps as done except the failing one
                    status = StepStatusSchema.SKIPPED
                else:
                    status = StepStatusSchema.PENDING

            # Parse timestamps
            started_at = None
            completed_at = None
            duration_ms = None

            if step_data.get("started_at"):
                with contextlib.suppress(ValueError, AttributeError):
                    started_at = datetime.fromisoformat(
                        step_data["started_at"].replace("Z", "+00:00")
                    )

            if step_data.get("completed_at"):
                with contextlib.suppress(ValueError, AttributeError):
                    completed_at = datetime.fromisoformat(
                        step_data["completed_at"].replace("Z", "+00:00")
                    )

            if step_data.get("duration_ms"):
                duration_ms = step_data["duration_ms"]
                total_duration_ms += duration_ms

            # Get error message if any
            # Handle both dict {"error": "msg"} and plain string formats
            if error_data:
                if isinstance(error_data, dict):
                    error = error_data.get("error")
                else:
                    error = str(error_data)
            else:
                error = None

            steps.append(
                ProcessingStepInfo(
                    step=ProcessingStepSchema(step_name),
                    status=status,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                    error=error,
                )
            )

        # Map current_step string to enum
        try:
            current_step = ProcessingStepSchema(document.current_step)
        except ValueError:
            current_step = ProcessingStepSchema.COMPLETE

        return DocumentProcessingDetails(
            id=document.id,
            original_filename=document.original_filename,
            file_type=self._get_file_type(document.mime_type),
            file_size=document.file_size_bytes,
            status=document.status,
            current_step=current_step,
            chunk_count=document.chunk_count if document.chunk_count > 0 else None,
            total_duration_ms=total_duration_ms if total_duration_ms > 0 else None,
            steps=steps,
            created_at=document.created_at,
            processing_started_at=document.processing_started_at,
            processing_completed_at=document.processing_completed_at,
        )

    async def get_by_id(self, doc_id: UUID) -> Document | None:
        """Get a document by ID.

        Args:
            doc_id: The Document UUID.

        Returns:
            Document or None if not found.
        """
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def archive(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> Document:
        """Archive a completed document (soft-delete without removing data).

        Sets archived_at timestamp and updates Qdrant payload to exclude
        from search results while preserving data for potential restoration.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting archive.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is not in READY status.
        """
        from qdrant_client.http import models as qdrant_models

        from app.integrations.qdrant_client import qdrant_service

        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # AC2: Only READY documents can be archived
        if document.status != DocumentStatus.READY:
            raise DocumentValidationError(
                code="INVALID_STATUS",
                message="Only completed (READY) documents can be archived",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # AC3: Check not already archived
        if document.archived_at is not None:
            raise DocumentValidationError(
                code="ALREADY_ARCHIVED",
                message="Document is already archived",
                status_code=400,
            )

        # Set archived_at timestamp
        document.archived_at = datetime.now(UTC)

        # AC4: Update Qdrant payload with archived=true
        try:
            collection_name = f"kb_{kb_id}"
            # Update all points for this document with archived=true
            qdrant_service.client.set_payload(
                collection_name=collection_name,
                payload={"archived": True},
                points=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="document_id",
                            match=qdrant_models.MatchValue(value=str(doc_id)),
                        )
                    ]
                ),
                wait=True,
            )
            logger.info(
                "qdrant_archive_payload_updated",
                document_id=str(doc_id),
                kb_id=str(kb_id),
            )
        except Exception as e:
            logger.error(
                "qdrant_archive_payload_failed",
                document_id=str(doc_id),
                kb_id=str(kb_id),
                error=str(e),
            )
            # Continue with DB update even if Qdrant fails - can be synced later

        # AC5: Audit log with action="document.archived"
        await audit_service.log_event(
            action="document.archived",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "document_name": document.name,
            },
        )

        logger.info(
            "document_archived",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

        return document

    async def restore(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> Document:
        """Restore an archived document back to active status.

        Clears archived_at timestamp and updates Qdrant payload to include
        in search results again.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting restore.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                document is not archived, or name collision exists.
        """
        from qdrant_client.http import models as qdrant_models

        from app.integrations.qdrant_client import qdrant_service

        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # AC-6.2.2: Only archived documents can be restored
        if document.archived_at is None:
            raise DocumentValidationError(
                code="NOT_ARCHIVED",
                message="Only archived documents can be restored",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # AC-6.2.3: Name collision detection (case-insensitive)
        existing = await self.session.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                func.lower(Document.name) == func.lower(document.name),
                Document.id != document.id,
                Document.status.in_(
                    [
                        DocumentStatus.READY,
                        DocumentStatus.PENDING,
                        DocumentStatus.PROCESSING,
                    ]
                ),
                Document.deleted_at.is_(None),
                Document.archived_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise DocumentValidationError(
                code="NAME_COLLISION",
                message="Cannot restore: a document with this name already exists",
                status_code=409,
                details={"document_name": document.name},
            )

        # Clear archived_at timestamp
        document.archived_at = None

        # AC-6.2.4: Update Qdrant payload with archived=false (status=completed)
        try:
            collection_name = f"kb_{kb_id}"
            qdrant_service.client.set_payload(
                collection_name=collection_name,
                payload={"archived": False, "status": "completed"},
                points=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="document_id",
                            match=qdrant_models.MatchValue(value=str(doc_id)),
                        )
                    ]
                ),
                wait=True,
            )
            logger.info(
                "qdrant_restore_payload_updated",
                document_id=str(doc_id),
                kb_id=str(kb_id),
            )
        except Exception as e:
            logger.error(
                "qdrant_restore_payload_failed",
                document_id=str(doc_id),
                kb_id=str(kb_id),
                error=str(e),
            )
            # Rollback DB change if Qdrant fails
            document.archived_at = datetime.now(UTC)
            raise DocumentValidationError(
                code="RESTORE_FAILED",
                message="Failed to update search index during restore",
                status_code=500,
                details={"error": str(e)},
            ) from e

        # Audit log with action="document.restored"
        await audit_service.log_event(
            action="document.restored",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "document_name": document.name,
            },
        )

        logger.info(
            "document_restored",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

        return document

    async def purge_document(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
    ) -> None:
        """Permanently delete an archived document from all storage layers.

        Deletes from PostgreSQL, Qdrant (vectors), and MinIO (file).
        This operation is irreversible.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting purge.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is not archived.
        """
        from qdrant_client.http import models as qdrant_models

        from app.integrations.qdrant_client import qdrant_service

        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # AC-6.3.2: Only archived documents can be purged
        if document.archived_at is None:
            raise DocumentValidationError(
                code="NOT_ARCHIVED",
                message="Only archived documents can be purged",
                status_code=400,
                details={"current_status": document.status.value},
            )

        # Grace period check: document must be archived for N days before purge
        grace_days = settings.archive_grace_period_days
        if grace_days > 0:
            grace_threshold = datetime.now(UTC) - timedelta(days=grace_days)
            if document.archived_at > grace_threshold:
                days_remaining = (
                    document.archived_at
                    + timedelta(days=grace_days)
                    - datetime.now(UTC)
                ).days + 1
                raise DocumentValidationError(
                    code="GRACE_PERIOD_NOT_ELAPSED",
                    message=f"Document must be archived for {grace_days} days before purge",
                    status_code=400,
                    details={
                        "archived_at": document.archived_at.isoformat(),
                        "grace_period_days": grace_days,
                        "days_remaining": days_remaining,
                    },
                )

        doc_name = document.name
        file_path = document.file_path

        # AC-6.3.3: Multi-layer storage cleanup
        # 1. Delete from Qdrant (vectors) - graceful handling if not exists
        try:
            collection_name = f"kb_{kb_id}"
            qdrant_service.client.delete(
                collection_name=collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=str(doc_id)),
                            )
                        ]
                    )
                ),
                wait=True,
            )
            logger.info(
                "qdrant_vectors_deleted",
                document_id=str(doc_id),
                kb_id=str(kb_id),
            )
        except Exception as e:
            logger.warning(
                "qdrant_purge_cleanup_failed",
                document_id=str(doc_id),
                kb_id=str(kb_id),
                error=str(e),
            )
            # Continue even if Qdrant cleanup fails

        # 2. Delete from MinIO (file) - graceful handling if not exists
        if file_path:
            try:
                # Extract object_path from full path (bucket/object_path)
                # file_path format: kb-{uuid}/{doc_id}/{filename}
                parts = file_path.split("/", 1)
                object_path = parts[1] if len(parts) > 1 else file_path
                await minio_service.delete_file(kb_id, object_path)
                logger.info(
                    "minio_file_deleted",
                    document_id=str(doc_id),
                    file_path=file_path,
                )
            except Exception as e:
                logger.warning(
                    "minio_purge_cleanup_failed",
                    document_id=str(doc_id),
                    file_path=file_path,
                    error=str(e),
                )
                # Continue even if MinIO cleanup fails

        # 3. Delete from PostgreSQL (record)
        await self.session.delete(document)

        # Audit log with action="document.purged"
        await audit_service.log_event(
            action="document.purged",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "document_name": doc_name,
            },
        )

        logger.info(
            "document_purged",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            user_id=str(user.id),
        )

    async def bulk_purge(
        self,
        kb_id: UUID,
        document_ids: list[UUID],
        user: User,
    ) -> dict:
        """Bulk purge multiple archived documents.

        Args:
            kb_id: The Knowledge Base UUID.
            document_ids: List of document UUIDs to purge.
            user: The user requesting purge.

        Returns:
            Dict with purged count, skipped count, and skipped_ids.

        Raises:
            DocumentValidationError: If KB not found or no permission.
        """
        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Knowledge Base not found",
                status_code=404,
            )

        purged = 0
        skipped_ids = []

        for doc_id in document_ids:
            try:
                await self.purge_document(kb_id, doc_id, user)
                purged += 1
            except DocumentValidationError as e:
                if e.code in ("NOT_ARCHIVED", "NOT_FOUND"):
                    skipped_ids.append(str(doc_id))
                else:
                    raise

        return {
            "purged": purged,
            "skipped": len(skipped_ids),
            "skipped_ids": skipped_ids,
        }

    async def clear_failed_document(
        self,
        kb_id: UUID,
        doc_id: UUID,
        user: User,
        reason: str = "manual_clear",
    ) -> None:
        """Clear a failed document and all its partial artifacts.

        Removes partial vectors from Qdrant, file from MinIO, and record from PostgreSQL.
        This operation is irreversible.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            user: The user requesting clear.
            reason: Reason for clearing (manual_clear or duplicate_upload).

        Raises:
            DocumentValidationError: If document not found, no permission,
                or document is not in FAILED status.
        """
        from qdrant_client.http import models as qdrant_models

        from app.integrations.qdrant_client import qdrant_service

        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # AC-6.4.2: Only failed documents can be cleared
        if document.status != DocumentStatus.FAILED:
            raise DocumentValidationError(
                code="NOT_FAILED",
                message="Only failed documents can be cleared",
                status_code=400,
                details={"current_status": document.status.value},
            )

        doc_name = document.name
        file_path = document.file_path

        # AC-6.4.3: Remove all partial artifacts
        # 1. Delete partial vectors from Qdrant (may not exist)
        try:
            collection_name = f"kb_{kb_id}"
            qdrant_service.client.delete(
                collection_name=collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=str(doc_id)),
                            )
                        ]
                    )
                ),
                wait=True,
            )
            logger.info(
                "qdrant_partial_vectors_deleted",
                document_id=str(doc_id),
                kb_id=str(kb_id),
            )
        except Exception as e:
            logger.warning(
                "qdrant_clear_cleanup_failed",
                document_id=str(doc_id),
                kb_id=str(kb_id),
                error=str(e),
            )

        # 2. Delete file from MinIO (may not exist)
        if file_path:
            try:
                # Extract object_path from full path (bucket/object_path)
                # file_path format: kb-{uuid}/{doc_id}/{filename}
                parts = file_path.split("/", 1)
                object_path = parts[1] if len(parts) > 1 else file_path
                await minio_service.delete_file(kb_id, object_path)
                logger.info(
                    "minio_file_deleted",
                    document_id=str(doc_id),
                    file_path=file_path,
                )
            except Exception as e:
                logger.warning(
                    "minio_clear_cleanup_failed",
                    document_id=str(doc_id),
                    file_path=file_path,
                    error=str(e),
                )

        # 3. Delete PostgreSQL record
        await self.session.delete(document)

        # Audit log with action based on reason
        action = (
            "document.auto_cleared"
            if reason == "duplicate_upload"
            else "document.cleared"
        )
        await audit_service.log_event(
            action=action,
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "document_name": doc_name,
                "reason": reason,
            },
        )

        logger.info(
            "document_cleared",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            reason=reason,
            user_id=str(user.id),
        )

    async def update_tags(
        self,
        kb_id: UUID,
        doc_id: UUID,
        tags: list[str],
        user: User,
    ) -> Document:
        """Update document tags.

        Args:
            kb_id: The Knowledge Base UUID.
            doc_id: The Document UUID.
            tags: New list of tags.
            user: The user updating tags.

        Returns:
            The updated Document record.

        Raises:
            DocumentValidationError: If document not found, no permission,
                or permission denied.
        """
        # Check WRITE permission on KB
        has_permission = await self._check_kb_permission(kb_id, user)
        if not has_permission:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Get document
        result = await self.session.execute(
            select(Document).where(
                Document.id == doc_id,
                Document.kb_id == kb_id,
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentValidationError(
                code="NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        # Validate and normalize tags
        validated_tags = validate_tags(tags)

        # Update tags
        document.tags = validated_tags

        # Audit log
        await audit_service.log_event(
            action="document.tags_updated",
            resource_type="document",
            user_id=user.id,
            resource_id=doc_id,
            details={
                "kb_id": str(kb_id),
                "tags": validated_tags,
            },
        )

        logger.info(
            "document_tags_updated",
            document_id=str(doc_id),
            kb_id=str(kb_id),
            tags=validated_tags,
            user_id=str(user.id),
        )

        return document
